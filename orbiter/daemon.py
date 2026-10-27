"""
Orbiter Core Daemon
Handles low-level hardware reading, 60Hz velocity ticker, uinput translation,
and IPC server for the GUI.
"""
import sys
import os
import time
import socket
import select
import threading
import json
import evdev
from evdev import UInput, ecodes as e

from orbiter.config import ConfigManager, IPC_SOCKET
from orbiter.device import find_spacemouse_device, wait_for_device, detect_device_model, DEVICE_MODELS
from orbiter.actions import ALL_UINPUT_KEYS, execute_action
from orbiter.window_watcher import WindowWatcher
from orbiter.conflicts import spacenavd_running, check_spacenavd_conflict
from orbiter.i18n import init_from_config, tr

class OrbiterDaemon:
    def __init__(self):
        self.config_mgr = ConfigManager()
        self.config = self.config_mgr.config

        self.running = True
        self.device = None
        self.device_model = None
        self.vmouse = None

        # State
        self.axes = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.axes_lock = threading.Lock()
        self.active_profile = self.config_mgr.get_active_profile_name()
        self.mode_2d = self.config_mgr.get("mode_2d", True)
        self.base_speed = self.config_mgr.get("base_speed", 0.05)

        # IPC: all connected sockets for commands; only subscribers get live events
        self.ipc_clients = []
        self.ipc_subscribers = []
        self.ipc_lock = threading.Lock()

        # Window Watcher for Auto-Profile-Switching
        self.watcher = WindowWatcher(on_window_changed=self.on_active_window_changed)
        self.last_auto_switched_profile = None

    def on_active_window_changed(self, info):
        """Called when the user switches to another window."""
        w_class = info.get("class", "")
        w_title = info.get("title", "")
        target_profile = self.config_mgr.get_profile_for_window(w_class, w_title)
        if target_profile and target_profile != self.active_profile:
            print(tr("daemon.auto_profile", wclass=w_class, profile=target_profile))
            self.last_auto_switched_profile = target_profile
            self.switch_profile(target_profile)

    def reload_config(self):
        self.config = self.config_mgr.load()
        self.active_profile = self.config_mgr.get_active_profile_name()
        self.mode_2d = self.config_mgr.get("mode_2d", self.mode_2d)
        self.base_speed = self.config_mgr.get("base_speed", self.base_speed)
        print(tr("daemon.reload", profile=self.active_profile))

    def notify_profile_change(self, profile_name):
        try:
            # Dev repo: …/orbiter/data/icons/; package: /usr/share/icons/…/orbiter.svg
            repo_icon = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "icons", "orbiter.svg"
            )
            fhs_icon = "/usr/share/icons/hicolor/scalable/apps/orbiter.svg"
            icon_file = repo_icon if os.path.isfile(repo_icon) else (
                fhs_icon if os.path.isfile(fhs_icon) else "orbiter"
            )
            import subprocess
            subprocess.Popen([
                "notify-send",
                "-a", "Orbiter",
                "-i", icon_file,
                "-t", "1800",
                tr("daemon.notify_title"),
                tr("daemon.notify_body", profile=profile_name)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        self.broadcast_event({
            "type": "profile_changed",
            "profile": profile_name
        })

    def switch_profile(self, name):
        new_prof = self.config_mgr.set_active_profile(name)
        self.reload_config()
        self.notify_profile_change(new_prof)
        print(tr("daemon.profile", profile=new_prof))
        return new_prof

    def next_profile(self):
        new_prof = self.config_mgr.next_profile()
        self.reload_config()
        self.notify_profile_change(new_prof)
        print(tr("daemon.next_profile", profile=new_prof))
        return new_prof

    def prev_profile(self):
        new_prof = self.config_mgr.prev_profile()
        self.reload_config()
        self.notify_profile_change(new_prof)
        print(tr("daemon.prev_profile", profile=new_prof))
        return new_prof

    def speed_up(self):
        self.base_speed = min(self.base_speed * 1.25, 0.20)
        self.config_mgr.set("base_speed", self.base_speed)
        self.config_mgr.save()
        print(tr("daemon.speed_up", speed=self.base_speed))

    def speed_down(self):
        self.base_speed = max(self.base_speed * 0.80, 0.01)
        self.config_mgr.set("base_speed", self.base_speed)
        self.config_mgr.save()
        print(tr("daemon.speed_down", speed=self.base_speed))

    def toggle_2d(self):
        self.mode_2d = not self.mode_2d
        self.config_mgr.set("mode_2d", self.mode_2d)
        self.config_mgr.save()
        mode = tr("daemon.mode_active") if self.mode_2d else tr("daemon.mode_hybrid")
        print(tr("daemon.mode_2d", mode=mode))

    def setup_uinput(self):
        cap = {
            e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL, e.REL_HWHEEL],
            e.EV_KEY: ALL_UINPUT_KEYS
        }
        self.vmouse = UInput(cap, name="Orbiter SpaceMouse")
        print(tr("daemon.uinput"))

    def start_ipc_server(self):
        """Create a Unix domain socket for GUI communication."""
        if IPC_SOCKET.exists():
            IPC_SOCKET.unlink()

        # Restrict create mode before bind so the socket is never briefly wider
        old_umask = os.umask(0o077)
        try:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(str(IPC_SOCKET))
        finally:
            os.umask(old_umask)
        try:
            os.chmod(IPC_SOCKET, 0o600)
        except OSError:
            pass
        server.listen(5)
        server.setblocking(False)

        def _peer_uid_ok(conn):
            """Only accept clients running as the same uid as this daemon."""
            try:
                import struct
                # Linux struct ucred: pid, uid, gid
                raw = conn.getsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_PEERCRED,
                    struct.calcsize("3i"),
                )
                _pid, uid, _gid = struct.unpack("3i", raw)
                return uid == os.getuid()
            except Exception:
                return False

        def ipc_worker():
            while self.running:
                readable, _, _ = select.select([server] + self.ipc_clients, [], [], 0.5)
                for s in readable:
                    if s is server:
                        client, _ = server.accept()
                        if not _peer_uid_ok(client):
                            try:
                                client.close()
                            except Exception:
                                pass
                            continue
                        client.setblocking(False)
                        with self.ipc_lock:
                            self.ipc_clients.append(client)
                    else:
                        try:
                            data = s.recv(8192)
                            if not data:
                                self._drop_ipc_client(s)
                                continue
                            msg = data.decode("utf-8").strip()
                            if msg == "SUBSCRIBE":
                                with self.ipc_lock:
                                    if s not in self.ipc_subscribers:
                                        self.ipc_subscribers.append(s)
                                s.sendall(b"OK\n")
                            elif msg == "GET_STATUS":
                                override = self.config_mgr.get_model_override()
                                if override != "auto" and override in DEVICE_MODELS:
                                    effective_model = DEVICE_MODELS[override]
                                else:
                                    effective_model = self.device_model or detect_device_model(self.device)

                                active_win = self.watcher.get_active_window()
                                status = {
                                    "connected": self.device is not None,
                                    "device_name": self.device.name if self.device else "None",
                                    "model_id": effective_model["id"],
                                    "model_name": effective_model["name"],
                                    "model_buttons": effective_model["button_count"],
                                    "model_override": override,
                                    "auto_switch_enabled": self.config_mgr.is_auto_switch_enabled(),
                                    "active_window": active_win,
                                    "mode_2d": self.mode_2d,
                                    "base_speed": self.base_speed,
                                    "deadzone": self.config_mgr.get("deadzone", 18),
                                    "active_profile": self.config_mgr.get_active_profile_name(),
                                    "profiles": list(self.config_mgr.get_profiles().keys()),
                                    "spacenavd_conflict": spacenavd_running(),
                                }
                                s.sendall((json.dumps(status) + "\n").encode("utf-8"))
                            elif msg == "RELOAD":
                                self.reload_config()
                                s.sendall(b"OK\n")
                            elif msg == "TOGGLE_2D":
                                self.toggle_2d()
                                s.sendall(b"OK\n")
                            elif msg.startswith("SET_AUTO_SWITCH"):
                                parts = msg.split()
                                val = (parts[1].lower() == "true") if len(parts) > 1 else True
                                self.config_mgr.set_auto_switch_enabled(val)
                                s.sendall(b"OK\n")
                            elif msg.startswith("SET_MODEL_OVERRIDE"):
                                parts = msg.split()
                                m_id = parts[1] if len(parts) > 1 else "auto"
                                self.config_mgr.set_model_override(m_id)
                                s.sendall(b"OK\n")
                            elif msg.startswith("SWITCH_PROFILE"):
                                parts = msg.split(maxsplit=1)
                                target = parts[1] if len(parts) > 1 else "Standard"
                                self.switch_profile(target)
                                s.sendall(b"OK\n")
                            elif msg == "NEXT_PROFILE":
                                self.next_profile()
                                s.sendall(b"OK\n")
                            elif msg == "PREV_PROFILE":
                                self.prev_profile()
                                s.sendall(b"OK\n")
                        except Exception:
                            self._drop_ipc_client(s)

        t = threading.Thread(target=ipc_worker, daemon=True)
        t.start()

    def _drop_ipc_client(self, client):
        """Remove a socket from command and subscriber lists, then close it."""
        with self.ipc_lock:
            if client in self.ipc_clients:
                self.ipc_clients.remove(client)
            if client in self.ipc_subscribers:
                self.ipc_subscribers.remove(client)
        try:
            client.close()
        except Exception:
            pass

    def broadcast_event(self, event_data):
        """Send live events only to clients that sent SUBSCRIBE."""
        with self.ipc_lock:
            if not self.ipc_subscribers:
                return
            msg = (json.dumps(event_data) + "\n").encode("utf-8")
            dead = []
            for client in self.ipc_subscribers:
                try:
                    client.sendall(msg)
                except Exception:
                    dead.append(client)
            for d in dead:
                if d in self.ipc_subscribers:
                    self.ipc_subscribers.remove(d)
                if d in self.ipc_clients:
                    self.ipc_clients.remove(d)
                try:
                    d.close()
                except Exception:
                    pass

    def curve(self, val, deadzone):
        if abs(val) <= deadzone:
            return 0
        sign = 1 if val > 0 else -1
        d = abs(val) - deadzone
        return sign * (d + (d * d * 0.002))

    def ticker_loop(self):
        """60 Hz ticker for smooth pointer motion and strict scroll gating."""
        scroll_acc = 0.0
        last_move_time = 0.0

        while self.running:
            # Check for live config file edits
            if self.config_mgr.is_modified():
                self.reload_config()

            now = time.time()
            deadzone = self.config_mgr.get("deadzone", 18)
            scroll_deadzone = self.config_mgr.get("scroll_deadzone_twist", 90)
            scroll_speed = self.config_mgr.get("scroll_speed", 0.003)
            move_cooldown = self.config_mgr.get("move_cooldown", 0.15)
            tilt_blend = float(self.config_mgr.get("tilt_blend", 0.4))
            lift_scroll = bool(self.config_mgr.get("lift_scroll_enabled", True))
            lift_deadzone = self.config_mgr.get("scroll_deadzone_lift", 90)

            with self.axes_lock:
                if self.mode_2d:
                    raw_x = self.axes[0]
                    raw_y = self.axes[2]
                else:
                    # Pitch (3) / Roll (4) blend into pointer when hybrid is on
                    raw_x = self.axes[0] + int(self.axes[4] * tilt_blend)
                    raw_y = self.axes[2] - int(self.axes[3] * tilt_blend)
                raw_twist = self.axes[5]
                raw_lift = self.axes[1]

            cur_x = self.curve(raw_x, deadzone)
            cur_y = self.curve(raw_y, deadzone)

            dx = int(cur_x * self.base_speed)
            dy = int(cur_y * self.base_speed)

            moved = False
            if dx != 0:
                self.vmouse.write(e.EV_REL, e.REL_X, dx)
                moved = True
            if dy != 0:
                self.vmouse.write(e.EV_REL, e.REL_Y, dy)
                moved = True

            if moved:
                last_move_time = now
                scroll_acc = 0.0
                self.vmouse.syn()
            else:
                # Scroll only when pointer is idle and cooldown has elapsed
                if (now - last_move_time) > move_cooldown:
                    if abs(raw_twist) > scroll_deadzone:
                        twist_diff = raw_twist - (
                            scroll_deadzone if raw_twist > 0 else -scroll_deadzone
                        )
                        scroll_acc += twist_diff * scroll_speed
                    if lift_scroll and abs(raw_lift) > lift_deadzone:
                        # Positive lift (cap up) → scroll up (positive REL_WHEEL)
                        lift_diff = raw_lift - (
                            lift_deadzone if raw_lift > 0 else -lift_deadzone
                        )
                        scroll_acc += lift_diff * scroll_speed
                    ticks = int(scroll_acc)
                    if ticks != 0:
                        self.vmouse.write(e.EV_REL, e.REL_WHEEL, ticks)
                        self.vmouse.syn()
                        scroll_acc -= ticks

            time.sleep(1.0 / 60.0)

    def run(self):
        self.setup_uinput()
        self.start_ipc_server()
        self.watcher.start()

        ticker = threading.Thread(target=self.ticker_loop, daemon=True)
        ticker.start()

        state_callbacks = {
            "speed_up": self.speed_up,
            "speed_down": self.speed_down,
            "toggle_2d": self.toggle_2d,
            "next_profile": self.next_profile,
            "prev_profile": self.prev_profile,
            "switch_profile": self.switch_profile
        }

        print(tr("daemon.started"))

        while self.running:
            self.device = wait_for_device()
            self.device_model = detect_device_model(self.device)
            print(tr(
                "daemon.connected",
                name=self.device.name,
                model=self.device_model["name"],
                buttons=self.device_model["button_count"],
            ))

            try:
                for event in self.device.read_loop():
                    if not self.running:
                        break

                    if event.type == e.EV_REL:
                        with self.axes_lock:
                            if event.code in self.axes:
                                self.axes[event.code] = event.value
                        self.broadcast_event({
                            "type": "axis",
                            "code": event.code,
                            "value": event.value
                        })

                    elif event.type == e.EV_KEY:
                        btn_code_str = str(event.code)
                        buttons_cfg = self.config_mgr.get("buttons", {})
                        btn_def = buttons_cfg.get(btn_code_str)

                        self.broadcast_event({
                            "type": "button",
                            "code": event.code,
                            "value": event.value,
                            "name": btn_def.get("name", f"Taste {event.code}") if btn_def else f"Taste {event.code}"
                        })

                        if btn_def:
                            execute_action(
                                btn_def,
                                is_press=(event.value == 1),
                                vmouse=self.vmouse,
                                state_callbacks=state_callbacks
                            )

            except OSError as err:
                print(tr("daemon.lost", err=err))
                with self.axes_lock:
                    for code in self.axes:
                        self.axes[code] = 0
                self.device = None
                time.sleep(1.0)

        if self.vmouse:
            self.vmouse.close()
        if IPC_SOCKET.exists():
            IPC_SOCKET.unlink()

def main():
    init_from_config(ConfigManager())
    conflict = check_spacenavd_conflict()
    if conflict:
        print(tr("daemon.conflict", msg=conflict), file=sys.stderr)
        sys.exit(1)

    daemon = OrbiterDaemon()
    try:
        daemon.run()
    except KeyboardInterrupt:
        print(tr("daemon.stopped"))
        daemon.running = False

if __name__ == "__main__":
    main()

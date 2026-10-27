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
from orbiter.device import find_spacemouse_device, wait_for_device
from orbiter.actions import ALL_UINPUT_KEYS, execute_action

class OrbiterDaemon:
    def __init__(self):
        self.config_mgr = ConfigManager()
        self.config = self.config_mgr.config

        self.running = True
        self.device = None
        self.vmouse = None

        # State
        self.axes = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.axes_lock = threading.Lock()
        self.active_profile = self.config_mgr.get_active_profile_name()
        self.mode_2d = self.config_mgr.get("mode_2d", True)
        self.base_speed = self.config_mgr.get("base_speed", 0.05)

        # IPC Clients (GUI live monitor)
        self.ipc_clients = []
        self.ipc_lock = threading.Lock()

    def reload_config(self):
        self.config = self.config_mgr.load()
        self.active_profile = self.config_mgr.get_active_profile_name()
        self.mode_2d = self.config_mgr.get("mode_2d", self.mode_2d)
        self.base_speed = self.config_mgr.get("base_speed", self.base_speed)
        print(f"[Daemon] Konfiguration live neu geladen. Aktives Profil: {self.active_profile}")

    def notify_profile_change(self, profile_name):
        try:
            icon_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "icons", "orbiter.svg")
            import subprocess
            subprocess.Popen([
                "notify-send",
                "-a", "Orbiter",
                "-i", icon_file,
                "-t", "1800",
                "Orbiter Profil gewechselt",
                f"Aktiv: {profile_name}"
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
        print(f"[Daemon] Profil gewechselt zu: {new_prof}")
        return new_prof

    def next_profile(self):
        new_prof = self.config_mgr.next_profile()
        self.reload_config()
        self.notify_profile_change(new_prof)
        print(f"[Daemon] Nächstes Profil: {new_prof}")
        return new_prof

    def prev_profile(self):
        new_prof = self.config_mgr.prev_profile()
        self.reload_config()
        self.notify_profile_change(new_prof)
        print(f"[Daemon] Vorheriges Profil: {new_prof}")
        return new_prof

    def speed_up(self):
        self.base_speed = min(self.base_speed * 1.25, 0.20)
        self.config_mgr.set("base_speed", self.base_speed)
        self.config_mgr.save()
        print(f"[Daemon] Geschwindigkeit erhöht: {self.base_speed:.4f}")

    def speed_down(self):
        self.base_speed = max(self.base_speed * 0.80, 0.01)
        self.config_mgr.set("base_speed", self.base_speed)
        self.config_mgr.save()
        print(f"[Daemon] Geschwindigkeit verringert: {self.base_speed:.4f}")

    def toggle_2d(self):
        self.mode_2d = not self.mode_2d
        self.config_mgr.set("mode_2d", self.mode_2d)
        self.config_mgr.save()
        print(f"[Daemon] 2D-Modus: {'AKTIV' if self.mode_2d else 'HYBRID'}")

    def setup_uinput(self):
        cap = {
            e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL, e.REL_HWHEEL],
            e.EV_KEY: ALL_UINPUT_KEYS
        }
        self.vmouse = UInput(cap, name="Orbiter SpaceMouse")
        print("[Daemon] Virtuelles Eingabegerät 'Orbiter SpaceMouse' erstellt.")

    def start_ipc_server(self):
        """Erstellt einen Unix Domain Socket für Kommunikation mit der GUI."""
        if IPC_SOCKET.exists():
            IPC_SOCKET.unlink()

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(IPC_SOCKET))
        server.listen(5)
        server.setblocking(False)

        def ipc_worker():
            while self.running:
                readable, _, _ = select.select([server] + self.ipc_clients, [], [], 0.5)
                for s in readable:
                    if s is server:
                        client, _ = server.accept()
                        client.setblocking(False)
                        with self.ipc_lock:
                            self.ipc_clients.append(client)
                    else:
                        try:
                            data = s.recv(1024)
                            if not data:
                                with self.ipc_lock:
                                    if s in self.ipc_clients:
                                        self.ipc_clients.remove(s)
                                s.close()
                                continue
                            msg = data.decode("utf-8").strip()
                            if msg == "GET_STATUS":
                                status = {
                                    "connected": self.device is not None,
                                    "device_name": self.device.name if self.device else "None",
                                    "mode_2d": self.mode_2d,
                                    "base_speed": self.base_speed,
                                    "deadzone": self.config_mgr.get("deadzone", 18),
                                    "active_profile": self.config_mgr.get_active_profile_name(),
                                    "profiles": list(self.config_mgr.get_profiles().keys())
                                }
                                s.sendall((json.dumps(status) + "\n").encode("utf-8"))
                            elif msg == "RELOAD":
                                self.reload_config()
                                s.sendall(b"OK\n")
                            elif msg == "TOGGLE_2D":
                                self.toggle_2d()
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
                            with self.ipc_lock:
                                if s in self.ipc_clients:
                                    self.ipc_clients.remove(s)
                            s.close()

        t = threading.Thread(target=ipc_worker, daemon=True)
        t.start()

    def broadcast_event(self, event_data):
        """Sendet Live-Events an verbundene GUI-Monitore."""
        with self.ipc_lock:
            if not self.ipc_clients:
                return
            msg = (json.dumps(event_data) + "\n").encode("utf-8")
            dead = []
            for client in self.ipc_clients:
                try:
                    client.sendall(msg)
                except Exception:
                    dead.append(client)
            for d in dead:
                self.ipc_clients.remove(d)

    def curve(self, val, deadzone):
        if abs(val) <= deadzone:
            return 0
        sign = 1 if val > 0 else -1
        d = abs(val) - deadzone
        return sign * (d + (d * d * 0.002))

    def ticker_loop(self):
        """60 Hz Ticker für flüssigen Mauszeiger und strikte Scroll-Sperre."""
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

            with self.axes_lock:
                if self.mode_2d:
                    raw_x = self.axes[0]
                    raw_y = self.axes[2]
                else:
                    raw_x = self.axes[0] + int(self.axes[4] * 0.4)
                    raw_y = self.axes[2] - int(self.axes[3] * 0.4)
                raw_twist = self.axes[5]

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
                # Scrollen NUR wenn Zeiger steht und Cooldown abgelaufen ist
                if (now - last_move_time) > move_cooldown:
                    if abs(raw_twist) > scroll_deadzone:
                        twist_diff = raw_twist - (scroll_deadzone if raw_twist > 0 else -scroll_deadzone)
                        scroll_acc += twist_diff * scroll_speed
                        ticks = int(scroll_acc)
                        if ticks != 0:
                            self.vmouse.write(e.EV_REL, e.REL_WHEEL, ticks)
                            self.vmouse.syn()
                            scroll_acc -= ticks

            time.sleep(1.0 / 60.0)

    def run(self):
        self.setup_uinput()
        self.start_ipc_server()

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

        print("[Daemon] Orbiter Daemon gestartet. Warte auf 3Dconnexion-Hardware...")

        while self.running:
            self.device = wait_for_device()
            print(f"[Daemon] Verbunden mit: {self.device.name} ({self.device.path})")

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

            except (OSError, Exception) as err:
                print(f"[Daemon] Verbindung verloren ({err}). Warte auf Wiederverbindung...")
                self.device = None
                time.sleep(1.0)

        if self.vmouse:
            self.vmouse.close()
        if IPC_SOCKET.exists():
            IPC_SOCKET.unlink()

def main():
    daemon = OrbiterDaemon()
    try:
        daemon.run()
    except KeyboardInterrupt:
        print("\n[Daemon] Beendet durch Benutzer.")
        daemon.running = False

if __name__ == "__main__":
    main()

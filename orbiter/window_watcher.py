"""
Active Window Watcher & Event Listener for Linux Desktop (Hyprland, Wayland & X11)
Erkennt automatisch das aktive Programmfenster für dynamisches Profil-Switching.
"""
import os
import json
import shutil
import socket
import select
import threading
import subprocess
import time

class WindowWatcher:
    def __init__(self, on_window_changed=None):
        self.on_window_changed = on_window_changed
        self._running = False
        self._thread = None
        self._last_window_class = None
        self._desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        self._has_hyprctl = shutil.which("hyprctl") is not None
        self._has_xdotool = shutil.which("xdotool") is not None
        self._has_xprop = shutil.which("xprop") is not None

    def start(self):
        """Startet den Window-Watcher im Hintergrund-Thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="WindowWatcherThread")
        self._thread.start()

    def stop(self):
        """Stoppt die Überwachung."""
        self._running = False

    def get_active_window(self):
        """
        Fragt das aktuell fokussierte Fenster synchron ab.
        Gibt ein Dict zurück: {"class": ..., "title": ...}
        """
        # 1. Hyprland Abfrage
        if self._has_hyprctl:
            try:
                res = subprocess.run(
                    ["hyprctl", "activewindow", "-j"],
                    capture_output=True, text=True, timeout=0.5
                )
                if res.returncode == 0 and res.stdout.strip():
                    data = json.loads(res.stdout)
                    w_class = data.get("class") or data.get("initialClass") or ""
                    w_title = data.get("title") or data.get("initialTitle") or ""
                    if w_class:
                        return {"class": w_class.strip(), "title": w_title.strip()}
            except Exception:
                pass

        # 2. X11 / XWayland Fallback über xdotool
        if self._has_xdotool and self._has_xprop:
            try:
                wid_res = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, timeout=0.5)
                if wid_res.returncode == 0 and wid_res.stdout.strip():
                    wid = wid_res.stdout.strip()
                    xprop_res = subprocess.run(["xprop", "-id", wid, "WM_CLASS"], capture_output=True, text=True, timeout=0.5)
                    if xprop_res.returncode == 0 and "WM_CLASS" in xprop_res.stdout:
                        # Output form: WM_CLASS(STRING) = "gimp", "Gimp"
                        parts = [p.strip().strip('"') for p in xprop_res.stdout.split("=")[-1].split(",")]
                        if parts:
                            return {"class": parts[-1], "title": ""}
            except Exception:
                pass

        return {"class": "", "title": ""}

    def _run_loop(self):
        """Event-Loop: Nutzt Hyprland Socket2 falls vorhanden, sonst schlankes Polling."""
        # Prüfen auf Hyprland Event Socket (.socket2.sock)
        hypr_sock_path = self._find_hyprland_socket2()
        if hypr_sock_path and os.path.exists(hypr_sock_path):
            self._listen_hyprland_socket(hypr_sock_path)
        else:
            self._poll_fallback()

    def _find_hyprland_socket2(self):
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        if sig:
            cand = os.path.join(runtime_dir, "hypr", sig, ".socket2.sock")
            if os.path.exists(cand):
                return cand

        # Suche in /run/user/<uid>/hypr/*/
        hypr_base = os.path.join(runtime_dir, "hypr")
        if os.path.isdir(hypr_base):
            for entry in os.listdir(hypr_base):
                cand = os.path.join(hypr_base, entry, ".socket2.sock")
                if os.path.exists(cand):
                    return cand
        return None

    def _listen_hyprland_socket(self, sock_path):
        """Echtzeit-Event-Listener für Hyprland: 0% CPU, sofortige Reaktion."""
        while self._running:
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(sock_path)
                sock.settimeout(2.0)
                buffer = ""

                # Einmaliger Initial-Check
                info = self.get_active_window()
                self._dispatch(info)

                while self._running:
                    try:
                        data = sock.recv(2048)
                        if not data:
                            break
                        buffer += data.decode("utf-8", errors="ignore")
                        lines = buffer.split("\n")
                        buffer = lines[-1]

                        for line in lines[:-1]:
                            line = line.strip()
                            # Hyprland activewindow Event: activewindow>>windowclass,windowtitle
                            if line.startswith("activewindow>>"):
                                raw = line[14:]
                                parts = raw.split(",", 1)
                                w_class = parts[0].strip() if parts else ""
                                w_title = parts[1].strip() if len(parts) > 1 else ""
                                self._dispatch({"class": w_class, "title": w_title})
                            elif line.startswith("closewindow>>") or line.startswith("workspace>>"):
                                info = self.get_active_window()
                                self._dispatch(info)
                    except socket.timeout:
                        continue
                    except Exception:
                        break

                sock.close()
            except Exception:
                time.sleep(1.0)

            if not self._running:
                break
            time.sleep(0.5)

    def _poll_fallback(self):
        """Sanftes Polling (alle 400ms) für Umgebungen ohne Event-Socket."""
        while self._running:
            try:
                info = self.get_active_window()
                if info and info.get("class"):
                    self._dispatch(info)
            except Exception:
                pass
            time.sleep(0.4)

    def _dispatch(self, info):
        w_class = (info.get("class") or "").strip().lower()
        if not w_class:
            return
        if w_class != self._last_window_class:
            self._last_window_class = w_class
            if self.on_window_changed:
                try:
                    self.on_window_changed(info)
                except Exception as e:
                    print(f"[WindowWatcher] Callback-Fehler: {e}")

"""
Orbiter Unified Command Line Interface & Runner
"""
import sys
import socket
import json
import subprocess
from datetime import datetime
from pathlib import Path

from orbiter.config import ConfigManager, IPC_SOCKET
from orbiter.conflicts import spacenavd_running, check_spacenavd_conflict
from orbiter.i18n import init_from_config, tr


def send_ipc(command):
    if not IPC_SOCKET.exists():
        print(tr("cli.daemon_not_running"))
        return None
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(1.0)
        client.connect(str(IPC_SOCKET))
        client.sendall((command + "\n").encode("utf-8"))
        resp = client.recv(1024).decode("utf-8").strip()
        client.close()
        return resp
    except Exception as e:
        print(tr("cli.ipc_error", error=e))
        return None


def cmd_gui():
    from orbiter.gui.app import main as gui_main
    gui_main()


def cmd_daemon():
    conflict = check_spacenavd_conflict()
    if conflict:
        print(tr("conflict.error_prefix", msg=conflict), file=sys.stderr)
        sys.exit(1)
    from orbiter.daemon import main as daemon_main
    daemon_main()


def cmd_status():
    conflict_local = spacenavd_running()
    resp = send_ipc("GET_STATUS")
    if resp:
        try:
            st = json.loads(resp)
            print(tr("cli.status_title"))
            print(tr("cli.status_connected", val=tr("cli.status_yes") if st.get("connected") else tr("cli.status_no")))
            print(tr("cli.status_device", val=st.get("device_name")))
            print(tr("cli.status_profile", val=st.get("active_profile", "Standard")))
            print(tr("cli.status_profiles", val=", ".join(st.get("profiles", []))))
            print(tr("cli.status_2d", val=tr("cli.status_2d_active") if st.get("mode_2d") else tr("cli.status_2d_hybrid")))
            print(tr("cli.status_speed", val=f"{st.get('base_speed'):.4f}"))
            print(tr("cli.status_deadzone", val=st.get("deadzone")))
            conflict = st.get("spacenavd_conflict", conflict_local)
            print(tr(
                "cli.status_conflict",
                val=tr("cli.status_conflict_yes") if conflict else tr("cli.status_conflict_no"),
            ))
            if conflict:
                print("")
                print(check_spacenavd_conflict() or "")
        except Exception:
            print(resp)
    else:
        if conflict_local:
            print(tr("cli.status_title"))
            print(tr("cli.status_service"))
            print(tr("cli.status_conflict_please"))
            print("")
            print(check_spacenavd_conflict() or "")


def cmd_profile():
    if len(sys.argv) > 2:
        arg = " ".join(sys.argv[2:]).strip()
        if arg.lower() == "next":
            resp = send_ipc("NEXT_PROFILE")
            if resp == "OK":
                print(tr("cli.profile_next"))
        elif arg.lower() == "prev":
            resp = send_ipc("PREV_PROFILE")
            if resp == "OK":
                print(tr("cli.profile_prev"))
        else:
            resp = send_ipc(f"SWITCH_PROFILE {arg}")
            if resp == "OK":
                print(tr("cli.profile_switched", name=arg))
    else:
        resp = send_ipc("GET_STATUS")
        if resp:
            try:
                st = json.loads(resp)
                active = st.get("active_profile", "Standard")
                profs = st.get("profiles", [])
                print(tr("cli.profiles_title"))
                for p in profs:
                    prefix = "* " if p == active else "  "
                    suffix = tr("cli.active_suffix") if p == active else ""
                    print(f"{prefix}{p}{suffix}")
            except Exception:
                print(resp)


def cmd_toggle_2d():
    resp = send_ipc("TOGGLE_2D")
    if resp == "OK":
        print(tr("cli.2d_toggled"))


def cmd_reload():
    resp = send_ipc("RELOAD")
    if resp == "OK":
        print(tr("cli.reloaded"))


def cmd_restart():
    subprocess.run(["systemctl", "--user", "restart", "orbiter"], check=False)
    print(tr("cli.restarted"))


def cmd_config():
    mgr = ConfigManager()
    if len(sys.argv) < 3:
        print(tr("cli.config_usage"))
        return
    action = sys.argv[2].lower()
    if action == "export":
        if len(sys.argv) > 3:
            path = Path(sys.argv[3]).expanduser()
        else:
            stamp = datetime.now().strftime("%Y%m%d")
            path = Path.home() / f"orbiter-config-{stamp}.json"
        out = mgr.export_config(path)
        print(tr("cli.config_exported", path=out))
    elif action == "import":
        if len(sys.argv) < 4:
            print(tr("cli.config_import_need_path"), file=sys.stderr)
            sys.exit(1)
        path = Path(sys.argv[3]).expanduser()
        try:
            mgr.import_config(path)
        except Exception as e:
            print(tr("settings.import_fail", error=e), file=sys.stderr)
            sys.exit(1)
        send_ipc("RELOAD")
        print(tr("cli.config_imported", path=path))
    else:
        print(tr("cli.unknown", cmd=f"config {action}"))
        print(tr("cli.config_usage"))


def print_help():
    print(tr("cli.help"))


def main():
    init_from_config(ConfigManager())
    if len(sys.argv) < 2:
        cmd_gui()
        return

    sub = sys.argv[1].lower()
    if sub in ("gui", "ui", "settings", "--tray", "--minimized"):
        cmd_gui()
    elif sub in ("daemon", "server"):
        cmd_daemon()
    elif sub in ("status", "info"):
        cmd_status()
    elif sub in ("profile", "profiles"):
        cmd_profile()
    elif sub in ("2d", "toggle"):
        cmd_toggle_2d()
    elif sub in ("config",):
        cmd_config()
    elif sub in ("reload",):
        cmd_reload()
    elif sub in ("restart",):
        cmd_restart()
    elif sub in ("-h", "--help", "help"):
        print_help()
    else:
        print(tr("cli.unknown", cmd=sub))
        print_help()


if __name__ == "__main__":
    main()

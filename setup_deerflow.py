#!/usr/bin/env python3
"""
setup_deerflow.py
=================
One-time setup wizard for OCTO-Pro × DeerFlow integration.

Run this after cloning both repos:
    python setup_deerflow.py

What it does:
  1. Verifies DeerFlow is cloned alongside OCTO-Pro
  2. Copies / links the DeerFlow skills directory so the bridge can find them
  3. Optionally runs `make setup` for DeerFlow (interactive)
  4. Writes DeerFlow connection settings to config/api_keys.json
  5. Adds OCTO startup shortcut that launches both systems (Windows)
"""

import json
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEERFLOW_ROOT = ROOT / "deer-flow"
CONFIG_PATH   = ROOT / "config" / "api_keys.json"
SKILLS_LINK   = ROOT / "skills" / "deerflow"

RED   = "\033[91m"
GREEN = "\033[92m"
CYAN  = "\033[96m"
RESET = "\033[0m"

def log(msg):  print(f"{CYAN}[Setup]{RESET} {msg}")
def ok(msg):   print(f"{GREEN}[  OK]{RESET} {msg}")
def err(msg):  print(f"{RED}[FAIL]{RESET} {msg}")


def check_deerflow_clone():
    log("Checking DeerFlow clone...")
    if (DEERFLOW_ROOT / "Makefile").exists():
        ok(f"DeerFlow found at {DEERFLOW_ROOT}")
        return True
    print()
    log(f"DeerFlow not found at {DEERFLOW_ROOT}")
    ans = input("  Clone it now? [Y/n]: ").strip().lower()
    if ans in ("", "y", "yes"):
        subprocess.run(
            ["git", "clone", "https://github.com/bytedance/deer-flow.git",
             str(DEERFLOW_ROOT)],
            check=True
        )
        ok("DeerFlow cloned.")
        return True
    else:
        err("DeerFlow required for skill system. Some features will be unavailable.")
        return False


def link_skills():
    log("Linking DeerFlow skills catalog...")
    deerflow_skills = DEERFLOW_ROOT / "skills" / "public"
    if not deerflow_skills.exists():
        err(f"Skills not found at {deerflow_skills}"); return

    SKILLS_LINK.parent.mkdir(parents=True, exist_ok=True)
    if SKILLS_LINK.exists() or SKILLS_LINK.is_symlink():
        ok("Skills link already exists.")
        return

    try:
        SKILLS_LINK.symlink_to(deerflow_skills, target_is_directory=True)
        ok(f"Symlink created: {SKILLS_LINK} → {deerflow_skills}")
    except Exception:
        # Windows may need junction or copy
        try:
            import shutil
            shutil.copytree(str(deerflow_skills), str(SKILLS_LINK))
            ok(f"Skills copied to {SKILLS_LINK}")
        except Exception as e2:
            err(f"Could not link skills: {e2}")


def update_config():
    log("Updating config/api_keys.json with DeerFlow settings...")
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    cfg.setdefault("deerflow_base_url", "http://localhost:2026")
    cfg.setdefault("deerflow_enabled", True)

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    ok(f"Config updated: {CONFIG_PATH}")


def optional_deerflow_setup():
    log("Optional: Run DeerFlow setup wizard (make setup)?")
    ans = input("  [Y/n]: ").strip().lower()
    if ans not in ("", "y", "yes"):
        return
    try:
        subprocess.run(["make", "setup"], cwd=str(DEERFLOW_ROOT), check=False)
        ok("DeerFlow setup complete.")
    except FileNotFoundError:
        err("'make' not found — run 'make setup' manually in the deer-flow/ folder.")


def check_dependencies():
    log("Checking Python dependencies...")
    missing = []
    for pkg in ["httpx", "sounddevice", "google.genai"]:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    if missing:
        log(f"Missing packages: {', '.join(missing)}")
        log("Run: pip install -r requirements.txt")
    else:
        ok("All OCTO dependencies present.")


def print_summary(df_ok: bool):
    print()
    print("━" * 55)
    print("  OCTO-Pro × DeerFlow Setup Complete")
    print("━" * 55)
    print(f"  DeerFlow clone  : {'✅' if df_ok else '⚠️  (optional, skip for now)'}")
    print(f"  Skills catalog  : {'✅' if (SKILLS_LINK).exists() else '⚠️  not linked'}")
    print(f"  Config updated  : ✅")
    print()
    print("  To launch:")
    if platform.system() == "Windows":
        print("    start_octo_pro.bat")
    else:
        print("    ./start_octo_pro.sh")
    print()
    print("  Voice commands:")
    print("    'find a skill for data analysis'")
    print("    'research quantum computing in depth'")
    print("    'run a DeerFlow ultra task: build me a React dashboard'")
    print("    'list all skills'")
    print("━" * 55)


def main():
    print()
    print("  OCTO-Pro × DeerFlow Integration Setup")
    print("  ──────────────────────────────────────")
    print()
    df_ok = check_deerflow_clone()
    if df_ok:
        link_skills()
        optional_deerflow_setup()
    update_config()
    check_dependencies()
    print_summary(df_ok)


if __name__ == "__main__":
    main()

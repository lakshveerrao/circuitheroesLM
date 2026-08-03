#!/usr/bin/env python3
"""Official zero-clone installer for PBL · Projects by Laksh."""

from pathlib import Path
import io
import os
import platform
import shutil
import stat
import sys
import urllib.request
import zipfile


VERSION = "0.2.0"
ARCHIVE = f"https://github.com/lakshveerrao/circuitheroesLM/archive/refs/tags/pbl-v{VERSION}.zip"


def main() -> int:
    print(f"PBL · Projects by Laksh {VERSION}")
    print("Getting the versioned official portable package...")
    request = urllib.request.Request(ARCHIVE, headers={"User-Agent": "PBL-Installer"})
    with urllib.request.urlopen(request, timeout=60) as response:
        archive_bytes = response.read()
    if not archive_bytes.startswith(b"PK"):
        raise SystemExit("The official PBL package could not be verified as a ZIP archive.")

    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ProjectsByLaksh" / "PBL"
        bin_dir = base / "bin"
    else:
        base = Path.home() / ".local" / "share" / "projects-by-laksh" / "pbl"
        bin_dir = Path.home() / ".local" / "bin"
    destination = base / VERSION
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as package:
        root_name = package.namelist()[0].split("/")[0]
        members = [name for name in package.namelist() if name.startswith(root_name + "/") and not name.endswith("/")]
        for member in members:
            relative = Path(member).relative_to(root_name)
            if ".." in relative.parts:
                raise SystemExit("The official package contained an unsafe path.")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with package.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)

    bin_dir.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        launcher = bin_dir / "pbl.cmd"
        launcher.write_text(f'@echo off\r\n"{sys.executable}" "{destination / "pbl"}" %*\r\n', encoding="utf-8")
    else:
        launcher = bin_dir / "pbl"
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{destination / "pbl"}" "$@"\n', encoding="utf-8")
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Installed: {launcher}")
    print("Open a new terminal and run: pbl")
    if str(bin_dir) not in os.environ.get("PATH", "").split(os.pathsep):
        print(f"Add this directory to PATH once: {bin_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

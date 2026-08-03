"""Install and launch the version-matched Projects by Laksh terminal."""

from __future__ import annotations

import io
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Optional
import urllib.request
import zipfile

from . import __version__


REPOSITORY = "lakshveerrao/circuitheroesLM"
TAG = f"pbl-v{__version__}"
ARCHIVE_URL = f"https://github.com/{REPOSITORY}/archive/refs/tags/{TAG}.zip"


def cache_root() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        return base / "ProjectsByLaksh" / "PBL" / "packages"
    base = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return base / "projects-by-laksh" / "pbl" / "packages"


def payload_directory() -> Path:
    return cache_root() / __version__


def _safe_relative(member: str, archive_root: str) -> Optional[Path]:
    if member.endswith("/") or not member.startswith(archive_root + "/"):
        return None
    relative = Path(member).relative_to(archive_root)
    if not relative.parts or ".." in relative.parts or relative.is_absolute():
        raise RuntimeError("The official PBL archive contained an unsafe path.")
    return relative


def _download_archive() -> bytes:
    request = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": f"pbl-lm/{__version__}"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except Exception as python_error:
        # Some macOS Python installers do not inherit the operating system's
        # certificate store. Fall back to the platform downloader without
        # requiring the user to repair Python or type a second command.
        with tempfile.TemporaryDirectory(prefix="pbl-download-") as temporary:
            archive = Path(temporary) / "pbl.zip"
            curl = shutil.which("curl")
            if curl:
                result = subprocess.run(
                    [curl, "--fail", "--location", "--silent", "--show-error",
                     "--max-time", "120", "--output", str(archive), ARCHIVE_URL],
                    check=False,
                )
                if result.returncode == 0 and archive.is_file():
                    return archive.read_bytes()
            powershell = shutil.which("powershell") or shutil.which("pwsh")
            if powershell:
                result = subprocess.run(
                    [powershell, "-NoProfile", "-Command",
                     "Invoke-WebRequest -UseBasicParsing -Uri $args[0] -OutFile $args[1]",
                     ARCHIVE_URL, str(archive)],
                    check=False,
                )
                if result.returncode == 0 and archive.is_file():
                    return archive.read_bytes()
        raise RuntimeError(
            "PBL needs an internet connection for its first launch. "
            "Connect once and run 'pbl' again."
        ) from python_error


def install_payload() -> Path:
    destination = payload_directory()
    executable = destination / "pbl"
    if executable.is_file():
        return executable

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        recovery = destination.with_name(f"{destination.name}.incomplete-{int(time.time())}")
        destination.replace(recovery)
        print(f"Preserved an incomplete earlier setup at {recovery}")
    print(f"PBL · Projects by Laksh {__version__}")
    print("Preparing the official terminal for first use...")
    archive_bytes = _download_archive()
    if not archive_bytes.startswith(b"PK"):
        raise RuntimeError("The official PBL release was not a valid ZIP archive.")

    with tempfile.TemporaryDirectory(prefix="pbl-install-", dir=str(destination.parent)) as temporary:
        staging = Path(temporary) / "payload"
        staging.mkdir()
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as package:
            names = package.namelist()
            if not names:
                raise RuntimeError("The official PBL release was empty.")
            archive_root = names[0].split("/")[0]
            for member in names:
                relative = _safe_relative(member, archive_root)
                if relative is None:
                    continue
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
        if not (staging / "pbl").is_file():
            raise RuntimeError("The official release did not contain the PBL command.")
        staging.replace(destination)
    return executable


def main() -> int:
    if "--launcher-version" in sys.argv[1:]:
        print(f"pbl-lm {__version__}")
        return 0
    try:
        executable = install_payload()
    except RuntimeError as error:
        print(f"PBL setup error: {error}", file=sys.stderr)
        return 1
    os.execv(sys.executable, [sys.executable, str(executable), *sys.argv[1:]])
    return 0

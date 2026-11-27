"""Install a validated release before starting Jarvis."""
import os
import shutil
import socket
import subprocess
import sys
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from jarvis_release_check import FILES, check_release


def smoke_test(stage):
    probe = (
        "from streamlit.testing.v1 import AppTest\n"
        "app = AppTest.from_file('jarvis12.py').run(timeout=30)\n"
        "if app.exception: raise RuntimeError(str(app.exception[0].message))\n"
    )
    subprocess.run([sys.executable, "-c", probe], cwd=stage, check=True, timeout=45)


def apply_update(root, package, test=smoke_test):
    """Replace application files, restoring each changed file if installation fails."""
    for name in FILES:
        if not (root / name).is_file():
            raise FileNotFoundError(root / name)
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(("127.0.0.1", 8501)) == 0:
            raise RuntimeError("Sluit Jarvis af voordat je een release toepast.")
    backups = root / "backups"
    backups.mkdir(exist_ok=True)
    backup = backups / package.stem
    backup.mkdir()
    for name in FILES:
        shutil.copy2(root / name, backup / name)
    version_file = root / "data" / "installed_release.txt"
    version_file.parent.mkdir(exist_ok=True)
    changed = []
    with TemporaryDirectory(dir=root) as temporary:
        stage = Path(temporary)
        with zipfile.ZipFile(package) as archive:
            for name in FILES:
                data = archive.read(name)
                compile(data, name, "exec")
                (stage / name).write_bytes(data)
        for name in ("jarvis22_selfupgrade.py", "jarvis22_email.py"):
            if (root / name).is_file():
                shutil.copy2(root / name, stage / name)
        test(stage)
        try:
            for name in sorted(FILES):
                os.replace(stage / name, root / name)
                changed.append(name)
            stamp = stage / "installed_release.txt"
            stamp.write_text(package.stem.removeprefix("v") + "\n", encoding="utf-8")
            os.replace(stamp, version_file)
        except Exception:
            for name in reversed(changed):
                shutil.copy2(backup / name, stage / name)
                os.replace(stage / name, root / name)
            raise
    return backup


def update_before_start(root):
    stamp = root / "data" / "installed_release.txt"
    installed = stamp.read_text(encoding="utf-8").strip() if stamp.is_file() else "22.0.0"
    package = check_release(root, installed)
    if package:
        return apply_update(root, package)
    return None


if __name__ == "__main__":
    update_before_start(Path(__file__).resolve().parent)

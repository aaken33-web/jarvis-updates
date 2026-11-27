"""Check the fixed Jarvis release channel and stage a verified update package."""
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile

REPOSITORY = "aaken33-web/jarvis-updates"
LIMIT = 10 * 1024 * 1024
FILES = {
    "jarvis12.py", "jarvis13_agent.py", "jarvis22_tools.py",
    "jarvis22_media_inbox.py", "jarvis22_pc_updates.py", "jarvis22_youtube.py",
}


def read_url(url, limit):
    request = urllib.request.Request(url, headers={"User-Agent": "Jarvis22 Release Check"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Releasebestand overschrijdt de maximale grootte.")
    return data


def check_release(root, installed):
    metadata = json.loads(read_url(f"https://api.github.com/repos/{REPOSITORY}/releases/latest", 256_000))
    tag = metadata["tag_name"]
    if not re.fullmatch(r"v22\.\d{1,5}\.\d{1,5}", tag):
        raise ValueError("Release heeft geen ondersteund Jarvis22-versienummer.")
    if tuple(map(int, tag[1:].split("."))) <= tuple(map(int, installed.split("."))):
        return None
    assets = {asset["name"]: asset for asset in metadata["assets"]}
    name = "jarvis22-update.zip"
    asset = assets[name]
    digest = asset.get("digest", "")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest or ""):
        raise ValueError("GitHub geeft geen geldige SHA-256-controlesom.")
    url = f"https://github.com/{REPOSITORY}/releases/download/{tag}/{name}"
    if asset["browser_download_url"] != url:
        raise ValueError("Onverwachte downloadlocatie.")
    package = read_url(url, LIMIT)
    if "sha256:" + hashlib.sha256(package).hexdigest() != digest:
        raise ValueError("De controlesom van de download klopt niet.")
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        entries = archive.infolist()
        if len(entries) != len(FILES) or {entry.filename for entry in entries} != FILES:
            raise ValueError("Het pakket bevat onverwachte of ontbrekende bestanden.")
        if sum(entry.file_size for entry in entries) > LIMIT:
            raise ValueError("Uitgepakt releasepakket is te groot.")
        for entry in entries:
            compile(archive.read(entry), entry.filename, "exec")
    staging = root / "workspace" / "release_candidates"
    staging.mkdir(parents=True, exist_ok=True)
    target = staging / f"{tag}.zip"
    with NamedTemporaryFile(dir=staging, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(package)
            stream.close()
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    return target

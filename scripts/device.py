"""Build, install, launch and pull the iOS app over `xcrun devicectl`.

    uv run python scripts/device.py build
    uv run python scripts/device.py launch -- --asr-parity
    uv run python scripts/device.py pull parity.json data/derived/m6/
"""

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "ios" / "TilavetApp"
# Outside ~/Desktop: iCloud sync adds extended attributes that codesign rejects.
DERIVED = Path.home() / "Library" / "Caches" / "tilavet-ios"
BUNDLE_ID = "com.ismailcelik.tilavet"
DEVICE_NAME = "Fox"
POLL_S = 10.0


def device_id() -> str:
    with tempfile.NamedTemporaryFile(suffix=".json") as f:
        subprocess.run(["xcrun", "devicectl", "list", "devices", "--json-output", f.name], check=True,
                       capture_output=True)
        devices = json.loads(Path(f.name).read_text())["result"]["devices"]
    for d in devices:
        if d["deviceProperties"]["name"] == DEVICE_NAME:
            return d["hardwareProperties"]["udid"]
    raise SystemExit(f"no device named {DEVICE_NAME}")


def build() -> None:
    subprocess.run(["xcodegen", "generate", "--spec", str(APP_DIR / "project.yml")], check=True)
    subprocess.run(["xcodebuild", "-project", str(APP_DIR / "TilavetApp.xcodeproj"), "-scheme", "TilavetApp",
                    "-configuration", "Release", "-destination", f"id={device_id()}", "-derivedDataPath", str(DERIVED),
                    "-allowProvisioningUpdates", "-quiet", "build"], check=True)
    app = DERIVED / "Build" / "Products" / "Release-iphoneos" / "TilavetApp.app"
    subprocess.run(["xcrun", "devicectl", "device", "install", "app", "--device", device_id(), str(app)], check=True)


def launch(args: list[str]) -> None:
    subprocess.run(["xcrun", "devicectl", "device", "process", "launch", "--device", device_id(),
                    "--terminate-existing", BUNDLE_ID, *args], check=True)


def pull(source: str, destination: Path, wait: bool = False) -> Path:
    """Copy Documents/<source> from the app container; with `wait`, poll until it exists."""
    destination.mkdir(parents=True, exist_ok=True)
    while True:
        result = subprocess.run(["xcrun", "devicectl", "device", "copy", "from", "--device", device_id(),
                                 "--domain-type", "appDataContainer", "--domain-identifier", BUNDLE_ID,
                                 "--source", f"Documents/{source}", "--destination", str(destination / Path(source).name)],
                                capture_output=True, text=True)
        if result.returncode == 0:
            return destination / Path(source).name
        if not wait:
            raise SystemExit(result.stderr)
        time.sleep(POLL_S)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "launch", "pull"])
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.command == "build":
        build()
    elif args.command == "launch":
        launch([a for a in args.rest if a != "--"])
    else:
        print(pull(args.rest[0], Path(args.rest[1])))


if __name__ == "__main__":
    main()

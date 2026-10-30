"""Download Google's Hand Landmarker model, checking it before replacement."""

import argparse
import hashlib
from pathlib import Path
import tempfile
import urllib.request


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_SHA256 = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
DEFAULT_DESTINATION = Path(__file__).resolve().parents[1] / "assets" / "hand_landmarker.task"


def download_model(destination=DEFAULT_DESTINATION):
    destination = Path(destination).expanduser().resolve()
    if destination.is_file():
        if hashlib.sha256(destination.read_bytes()).hexdigest() == MODEL_SHA256:
            print(f"Model already verified: {destination}")
            return destination
        raise ValueError(
            f"Existing model has a different checksum: {destination}. "
            "Move it aside or choose --output PATH before downloading."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".download", delete=False) as target:
                temporary_path = Path(target.name)
                digest = hashlib.sha256()
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
                    digest.update(chunk)
        if digest.hexdigest() != MODEL_SHA256:
            raise ValueError("Downloaded model checksum does not match the verified model.")
        temporary_path.replace(destination)
        print(f"Downloaded and verified model: {destination}")
        return destination
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    try:
        download_model(args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"[ERROR] {error}\n")


if __name__ == "__main__":
    main()

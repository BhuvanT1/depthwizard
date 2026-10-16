"""
Fetch the source GeoTIFFs for the demo scenes into data/raw/.

The seven ~12.6 MB scene crops are published as assets on the repository's
`data-v1` GitHub Release rather than committed, so a clone stays small. Every
file is checked against a SHA-256 recorded here, so a truncated or substituted
download fails loudly instead of feeding wrong pixels into the pipeline.

    python scripts/download_data.py              # all scenes
    python scripts/download_data.py antakya fm   # just these

The synthetic regression scene (data/raw/synthetic.tif) is small and stays in
the repository; regenerate it with scripts/make_sample.py if needed.

Imagery: Maxar Open Data Program, CC BY-NC 4.0.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

RELEASE = "https://github.com/BhuvanT1/depthwizard/releases/download/data-v1"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

# scene -> (sha256, size in bytes)
SCENES = {
    "antakya":    ("77c5657f7583639710d1350c1d1f7e407f39ea0e735bfe88014afff68a1ef7d3", 12608550),
    "fm":         ("803864b5d6a1be51d0bf83ccaff9a0db6f9314e1fdede6f47ef2a5f57c7617c2", 12608549),
    "pg":         ("21a74e72a585c8e15a32cc685140dcc6fcb9e48cc7d2eb341d3259967883a5d1", 12608549),
    "atlas":      ("4e874c43dfc77c73e794ce5c0e983e35c2110c11381226fd0a0f999894110d6b", 12608549),
    "ian_forest": ("1adb814cf006222debaa1e4bc3985829749d9dcc0d2128706b1167b0e5dc0f3f", 12608549),
    "ian2":       ("7b31be00740858a91b7c7d6baa57ac6ebe105380c9324e202ed53f9a6ec374b0", 12608549),
    "capecoral":  ("978f4a27ec26023bea23cd72c8cc7b84c1f45e13158818290f8a091afdd895a0", 12608550),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(scene: str) -> None:
    digest, size = SCENES[scene]
    out = RAW / f"{scene}.tif"
    if out.exists() and out.stat().st_size == size and sha256(out) == digest:
        print(f"  {scene:<11} already present, checksum ok")
        return

    url = f"{RELEASE}/{scene}.tif"
    tmp = out.with_suffix(".tif.part")
    print(f"  {scene:<11} downloading {size / 1e6:.1f} MB ...", flush=True)
    with urllib.request.urlopen(url) as resp, open(tmp, "wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)

    got = sha256(tmp)
    if got != digest:
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"\nchecksum mismatch for {scene}.tif\n  expected {digest}\n  got      {got}")
    tmp.replace(out)
    print(f"  {scene:<11} ok")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("scenes", nargs="*", help=f"subset of: {' '.join(SCENES)}")
    args = ap.parse_args()

    unknown = [s for s in args.scenes if s not in SCENES]
    if unknown:
        sys.exit(f"unknown scene(s): {' '.join(unknown)}\nchoose from: {' '.join(SCENES)}")

    RAW.mkdir(parents=True, exist_ok=True)
    print(f"writing to {RAW}")
    for scene in args.scenes or SCENES:
        fetch(scene)


if __name__ == "__main__":
    main()

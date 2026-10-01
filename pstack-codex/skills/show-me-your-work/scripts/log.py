"""Append one decision row. Usage: python log.py file phase decision why evidence result."""
import sys
from datetime import datetime, timezone
from pathlib import Path


def clean(value):
    value = value.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def append(path, cells):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Append even if a header check fails; existing evidence must survive.
    header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as stream:
        if header:
            stream.write("ts\tphase\tdecision\twhy\tevidence\tresult\n")
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        stream.write("\t".join([stamp, *(clean(cell) for cell in cells)]) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 7:
        sys.exit("usage: python log.py file phase decision why evidence result")
    append(sys.argv[1], sys.argv[2:])

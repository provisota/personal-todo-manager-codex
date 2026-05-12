"""Generate a new Alembic migration with sequential NNNN_ numbering."""

import re
import subprocess
import sys
from pathlib import Path

VERSIONS_DIR = Path(__file__).parent.parent / "alembic" / "versions"


def next_seq() -> str:
    nums = []
    for f in VERSIONS_DIR.glob("*.py"):
        m = re.match(r"^(\d{4})_", f.name)
        if m:
            nums.append(int(m.group(1)))
    return f"{(max(nums) + 1) if nums else 1:04d}"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/new_migration.py <description>")
        sys.exit(1)

    description = "_".join(sys.argv[1:])
    seq = next_seq()
    rev_id = f"{seq}_{description}"

    cmd = [
        "alembic", "revision", "--autogenerate",
        "-m", description,
        "--rev-id", rev_id,
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

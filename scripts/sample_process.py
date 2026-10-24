"""Sample CPU % and RSS of a running process until it exits.

    uv run python scripts/sample_process.py <pid>
"""

import argparse
import statistics
import subprocess
import time

INTERVAL_S = 5.0
KB_PER_MB = 1024


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pid", type=int)
    args = parser.parse_args()

    cpu, rss = [], []
    while True:
        result = subprocess.run(["ps", "-o", "%cpu=,rss=", "-p", str(args.pid)], capture_output=True, text=True)
        if result.returncode != 0:
            break

        # macOS prints the decimal separator of the user's locale.
        c, r = result.stdout.split()
        cpu.append(float(c.replace(",", ".")))
        rss.append(int(r) / KB_PER_MB)
        time.sleep(INTERVAL_S)

    if not cpu:
        raise SystemExit(f"no process {args.pid}")

    print(f"samples {len(cpu)}, CPU median {statistics.median(cpu):.1f}% max {max(cpu):.1f}%, "
          f"RSS max {max(rss):.0f} MB")


if __name__ == "__main__":
    main()

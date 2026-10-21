import argparse
import os
import sys
from pathlib import Path

from candidate import checkout, prepare, set_changed
from publish import publish


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "checkout", "publish"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root, output = Path.cwd(), args.directory.resolve()
    if args.command == "prepare":
        set_changed(prepare(root, output))
    elif args.command == "checkout":
        checkout(root, output)
    else:
        publish(root, output, os.environ.get("UPSTREAM_UPDATE_TOKEN", ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Upstream core update stopped: {error}", file=sys.stderr)
        sys.exit(1)

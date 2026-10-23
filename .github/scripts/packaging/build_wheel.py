import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Build a wheel from the source distribution")
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    output = args.output.resolve()
    subprocess.run(["uv", "build", "--sdist", "--python", "3.14", "--out-dir", str(output)], check=True)
    archives = list(output.glob("*.tar.gz"))
    if len(archives) != 1:
        raise RuntimeError("use an output directory containing one source distribution")
    subprocess.run(
        ["uv", "build", str(archives[0]), "--wheel", "--python", "3.14", "--out-dir", str(output)],
        check=True,
    )


if __name__ == "__main__":
    main()

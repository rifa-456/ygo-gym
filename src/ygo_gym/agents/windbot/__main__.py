import argparse

from . import available_decks, build


def main():
    parser = argparse.ArgumentParser(
        description="Build the optional WindBot worker or list its executors"
    )
    parser.add_argument("operation", choices=("build", "list"))
    parser.add_argument("--root")
    parser.add_argument("--dotnet", default="dotnet")
    args = parser.parse_args()
    if args.operation == "build":
        print(build(args.root, dotnet=args.dotnet))
    else:
        for entry in available_decks(args.root, dotnet=args.dotnet):
            print(
                f"{entry.id}\t{entry.name}\t{'ready' if entry.available else 'missing deck file'}"
            )


if __name__ == "__main__":
    main()

import sys


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python -m benchmarks.cloning {timing,memory} [options]")
        print("timing: pyperf calibration, worker processes, raw results, and comparisons")
        print("memory: isolated retained-clone memory measurements")
        return
    command = sys.argv.pop(1)
    if command == "timing":
        from .timing import main as run
    elif command == "memory":
        from .memory import main as run
    else:
        raise SystemExit(f"Unknown benchmark command: {command}; choose timing or memory")
    run()


if __name__ == "__main__":
    main()

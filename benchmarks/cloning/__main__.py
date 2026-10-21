import sys


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python -m benchmarks.cloning {timing,memory,profile} [options]")
        print("timing: pyperf calibration, worker processes, raw results, and comparisons")
        print("memory: isolated retained-clone memory measurements")
        print("profile: single-process workload and opt-in native clone diagnostics")
        return
    command = sys.argv.pop(1)
    if command == "timing":
        from .timing import main as run
    elif command == "memory":
        from .memory import main as run
    elif command == "profile":
        from .profile import main as run
    else:
        raise SystemExit(f"Unknown benchmark command: {command}; choose timing, memory or profile")
    run()


if __name__ == "__main__":
    main()

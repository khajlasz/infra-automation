"""Command-line entry point for Infrastructure Automation."""

import argparse


def main() -> int:
    """Run the initial command-line interface."""
    parser = argparse.ArgumentParser(
        description="Infrastructure Automation Framework"
    )
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

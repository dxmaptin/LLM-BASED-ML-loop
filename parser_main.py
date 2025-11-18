#!/usr/bin/env python3
"""Helper CLI to run only the parser agent and dump its selections."""

from agent_estimator.orchestrator import generate_context_summary


def main() -> None:
    generate_context_summary()


if __name__ == "__main__":
    main()

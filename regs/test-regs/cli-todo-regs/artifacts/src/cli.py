"""CLI entry point for the todo application.

Usage:
    python -m src.cli add "Buy groceries" --priority high
    python -m src.cli list --status pending
    python -m src.cli complete 1
"""

import argparse
import sys

from .todo import TodoStore


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="cli-todo",
        description="A command-line todo list application.",
    )
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )

    # --- add ---
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", type=str, help="The task title")
    add_parser.add_argument(
        "--priority",
        type=str,
        choices=["low", "medium", "high"],
        default="medium",
        help="Task priority (default: medium)",
    )

    # --- list ---
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "--status",
        type=str,
        choices=["all", "pending", "completed"],
        default="all",
        help="Filter tasks by status (default: all)",
    )

    # --- complete ---
    complete_parser = subparsers.add_parser(
        "complete", help="Mark a task as completed"
    )
    complete_parser.add_argument(
        "id", type=int, help="The task ID to complete"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    store = TodoStore()

    if args.command == "add":
        try:
            task = store.add_task(title=args.title, priority=args.priority)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(
            f'Task {task["id"]} added: "{task["title"]}"'
            f' [priority: {task["priority"]}]'
        )
        return 0

    if args.command == "list":
        try:
            tasks = store.list_tasks(status_filter=args.status)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        if not tasks:
            print("No tasks found.")
            return 0

        for task in tasks:
            status_marker = "x" if task["status"] == "completed" else " "
            print(
                f'[{status_marker}] {task["id"]}. {task["title"]} '
                f'(priority: {task["priority"]})'
            )
        return 0

    if args.command == "complete":
        try:
            task = store.complete_task(task_id=args.id)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f'Task {task["id"]} completed: "{task["title"]}"')
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

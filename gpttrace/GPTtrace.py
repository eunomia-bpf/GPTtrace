#! /bin/env python
import argparse
import os
import pathlib

from gpttrace.cmd import cmd
from gpttrace.execute import execute
from gpttrace.utils.common import pretty_print


def main() -> None:
    """
    Program entry.
    """
    parser = argparse.ArgumentParser(
        prog="GPTtrace",
        description="Use ChatGPT to write eBPF programs (bpftrace, etc.)",
    )
    parser.add_argument(
        "-c", "--cmd",
        help="Use the bcc tool to complete the trace task",
        nargs=2,
        metavar=("CMD_NAME", "QUERY"))
    parser.add_argument(
        "-v", "--verbose",
        help="Show more details",
        action="store_true")
    parser.add_argument(
        "-k", "--key",
        help="Openai api key, see `https://platform.openai.com/docs/quickstart/add-your-api-key` or passed through `OPENAI_API_KEY`",
        metavar="OPENAI_API_KEY")
    parser.add_argument('input_string', type=str, help='Your question or request for a bpf program')
    args = parser.parse_args()

    if os.getenv('OPENAI_API_KEY', args.key) is None:
        print(f"Either provide your access token through `-k` or through environment variable {OPENAI_API_KEY}")
        return
    if args.cmd is not None:
        cmd(args.cmd[0], args.cmd[1], args.verbose)
    elif args.input_string is not None:
        execute(args.input_string, args.verbose)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

#! /bin/env python
import argparse
import os
import pathlib

from gpttrace.cmd import cmd
from gpttrace.execute import execute
from gpttrace.generate import generate
from gpttrace.utils.common import get_doc_content_for_query, init_conversation, pretty_print

OPENAI_API_KEY = "OPENAI_API_KEY"
PROMPTS_DIR = pathlib.Path("./prompts")
DOC_PATH = "./bpf_tutorial/src"
LOCAL_PATH = pathlib.Path(__file__).resolve().parent

def main() -> None:
    """
    Program entry.
    """
    parser = argparse.ArgumentParser(
        prog="GPTtrace",
        description="Use ChatGPT to write eBPF programs (bpftrace, etc.)",
    )
    parser.add_argument(
        "-i", "--info",
        help="Let ChatGPT explain what's eBPF",
        action="store_true")
    parser.add_argument(
        "-c", "--cmd",
        help="Use the bcc tool to complete the trace task",
        nargs=2,
        metavar=("CMD_NAME", "QUERY"))
    parser.add_argument(
        "-e", "--execute",
        help="Generate commands using your input with ChatGPT, and run it",
        metavar="EXEC_QUERY")
    parser.add_argument(
        "-g", "--generate",
        help="Generate eBPF programs using your input with ChatGPT",
        metavar="GEN_QUERY")
    parser.add_argument(
        "-v", "--verbose",
        help="Show more details",
        action="store_true")
    parser.add_argument(
        "-k", "--key",
        help=f"Openai api key, see `https://platform.openai.com/docs/quickstart/add-your-api-key` or passed through `{OPENAI_API_KEY}`",
        metavar="OPENAI_API_KEY")
    parser.add_argument(
        "-t", "--train",
        help="Train ChatGPT with conversions we provided",
        action="store_true")
    args = parser.parse_args()

    if os.getenv(OPENAI_API_KEY, args.key) is None:
        print(f"Either provide your access token through `-k` or through environment variable {OPENAI_API_KEY}")
        return

    if args.info:
        user_input = "Explain what's eBPF"
        agent_chain, index = init_conversation(args.train, args.verbose)
        if args.train:
            info = get_doc_content_for_query(index, user_input)
            if info is not None:
                user_input = user_input + info
        response = agent_chain.predict(input=user_input)
        pretty_print(response)
    elif args.cmd is not None:
        cmd(args.cmd[0], args.cmd[1], args.verbose)
    elif args.execute is not None:
        execute(args.execute, args.train, args.verbose)
    elif args.generate is not None:
        generate(args.generate, args.train, args.verbose)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

#! /bin/env python3
import argparse
import os
import pathlib
import tempfile
import shutil
import pygments

from marko.block import FencedCode
from marko.inline import RawText
from marko.parser import Parser
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import PygmentsTokens
from pygments_markdown_lexer import MarkdownLexer
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import OpenAI
from langchain.agents import initialize_agent
from langchain.chains import ConversationChain
from langchain.agents import Tool
from llama_index import GPTSimpleVectorIndex, SimpleDirectoryReader

OPENAI_API_KEY = "OPENAI_API_KEY"
PROMPTS_DIR = pathlib.Path("./prompts")
DOC_PATH = "./prompts"
LOCAL_PATH = pathlib.Path(__file__).resolve().parent

def pretty_print(input, lexer=MarkdownLexer, *args, **kwargs):
    tokens = list(pygments.lex(input, lexer=lexer()))
    print_formatted_text(PygmentsTokens(tokens), *args, **kwargs)

def main():
    parser = argparse.ArgumentParser(
        prog="GPTtrace",
        description="Use ChatGPT to write eBPF programs (bpftrace, etc.)",
    )

    group = parser
    group.add_argument(
        "-i", "--info", help="Let ChatGPT explain what's eBPF", action="store_true")
    group.add_argument(
        "-e", "--execute",
        help="Generate commands using your input with ChatGPT, and run it",
        action="store", metavar="TEXT")
    group.add_argument(
        "-g", "--generate", help="Generate eBPF programs using your input with ChatGPT", action="store", metavar="TEXT")
    parser.add_argument(
        "-v", "--verbose", help="Show more details", action="store_true")
    parser.add_argument(
        "-k", "--key",
        help=f"openai api key, see `https://platform.openai.com/docs/quickstart/add-your-api-key` or passed through `{OPENAI_API_KEY}`")
    group.add_argument(
        "-t", "--train", help="Train ChatGPT with conversions we provided", action="store_true")
    args = parser.parse_args()
    opeanai_api_key = args.key or os.environ.get(OPENAI_API_KEY, None)
    if opeanai_api_key is None:
        print(
            f"Either provide your access token through `-t` or through environment variable {OPENAI_API_KEY}"
        )
        return
    query_gpt = init(args.verbose, args.train)
    if args.info:
        response = query_gpt(input="Explain what's eBPF")
        pretty_print(response)
    elif args.execute is not None:
        user_input = args.execute
        execute(query_gpt, user_input, args.verbose)
    elif args.generate is not None:
        desc: str = args.generate
        print("Sending query to ChatGPT: " + desc)
        response = query_gpt(input=construct_generate_prompt(desc))
        pretty_print(response)
        parsed = extract_code_blocks(response)
        with open("generated.bpf.c", "w") as f:
            for code in parsed:
                f.write(code)
    else:
        parser.print_help()


def construct_generate_prompt(text: str) -> str:
    return f"""You are now a translater from human language to {os.uname()[0]} eBPF programs.
Please write eBPF programs for me.
No explanation required, no instruction required, don't tell me how to compile and run.
What I want is just a eBPF program with markdown format for: {text}."""

def construct_running_prompt(text: str) -> str:
    return f"""You are now a translater from human language to {os.uname()[0]} shell bpftrace command.
No explanation required.
Respond with only the raw shell bpftrace command.
It should be start with `bpftrace`.
Your response should be able to put into a shell and run directly.
Just output in one line, without any description, or any other text that cannot be run in shell.
What should I type to shell to trace using bpftrace for: {text}, in one line."""


def make_executable_command(command: str) -> str:
    if command.startswith("\n"):
        command = command[1:]
    if command.endswith("\n"):
        command = command[:-1]
    if command.startswith("`"):
        command = command[1:]
    if command.endswith("`"):
        command = command[:-1]
    command = command.strip()
    command = command.split("User: ")[0]
    return command

def init(verbose: bool, need_train: bool) -> function:
    llm = OpenAI(temperature=0)
    if need_train:
        if not os.path.exists(f"{LOCAL_PATH}/train_data.json"):
            print(f"{LOCAL_PATH}/train_data.josn not found. Training...")
            documents = SimpleDirectoryReader(str(DOC_PATH)).load_data()
            index = GPTSimpleVectorIndex(documents)
            index.save_to_disk(f"{LOCAL_PATH}/train_data.json")
            print(f"Training completed, {LOCAL_PATH}/train_data.josn has been saved.")
        else:
            index = GPTSimpleVectorIndex.load_from_disk(f"{LOCAL_PATH}/train_data.json")
        # tools = load_tools(["serpapi", "llm-math"], llm=llm)
        tool = Tool(
            name = "ebpf generator",
            func=lambda q: str(index.query(q)),
            description="Generate eBPF programs and tracing with ChatGPT and natural language",
            return_direct=True)
        memory = ConversationBufferMemory(memory_key="chat_history")
        agent_chain = initialize_agent([tool], llm, 
                                       agent="conversational-react-description", 
                                       memory=memory, verbose=verbose)
        query_gpt = agent_chain.run
    else:
        agent_chain = ConversationChain(
                        llm=llm,
                        verbose=True,
                        memory=ConversationBufferMemory())
        query_gpt = agent_chain.predict
    return query_gpt

def execute(query_gpt: function, user_input: str, verbose: bool) -> None:
    print("Sending query to ChatGPT: " + user_input)
    prompt = construct_running_prompt(user_input)
    response = query_gpt(input=prompt)
    parsed = make_executable_command(response)
    print(f"The command generated by gpt is: {parsed}")
    print("Press Ctrl+C to stop the command....")
    ok = False
    for _ in range(1, 5+1):
        stderr_out = tempfile.mktemp()
        if os.system(f"sudo {parsed} 2> {stderr_out}") != 0:
            with open(stderr_out, "r") as f:
                stderr_content = f.read()
            print("Failed to run: ")
            print(stderr_content)
            print(
                f"Failed to run bpftrace with generated command: {parsed}, sending errors to ChatGPT and re-train....")
            response = query_gpt(
                input=f"bpftrace gives me the following error on command you generated: {stderr_content}, please fix the command according to this error.")
            parsed = make_executable_command(response)
            if verbose:
                print(response)
            if not parsed.startswith("bpftrace"):
                continue
        else:
            ok = True
        shutil.rmtree(stderr_out, True)
    if not ok:
        print("Retry times exceeded..")

def extract_code_blocks(text: str) -> list[str]:
    result = []
    parser = Parser()
    for block in parser.parse(text).children:
        if type(block) is FencedCode:
            block: FencedCode
            blk: RawText = block.children[0]
            result.append(blk.children)
    return result

if __name__ == "__main__":
    main()

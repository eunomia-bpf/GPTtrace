#! /bin/env python
import argparse
import os
import pathlib
import tempfile
import shutil
from langchain import OpenAI
import pygments

from marko.block import FencedCode
from marko.inline import RawText
from marko.parser import Parser
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import PygmentsTokens
from pygments_markdown_lexer import MarkdownLexer
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.chains import ConversationChain
from langchain.agents import Tool
from llama_index import LLMPredictor, ServiceContext, StorageContext, VectorStoreIndex, SimpleDirectoryReader, load_index_from_storage
from command import cmd_parser 

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

    if args.key is not None:
        os.environ["OPENAI_API_KEY"] = args.key
    if os.environ.get(OPENAI_API_KEY, None) is None:
        print(f"Either provide your access token through `-k` or through environment variable {OPENAI_API_KEY}")
        return
    agent_chain, index = init(args.train, args.verbose)
    if args.info:
        user_input = "Explain what's eBPF"
        if args.train:
            info = get_doc_content_for_query(index, user_input)
            if info is not None:
                user_input = user_input + info
        response = agent_chain.predict(input=user_input)
        pretty_print(response)
    elif args.cmd is not None:
        cmd_parser(args.cmd[0], args.cmd[1], args.verbose)
    elif args.execute is not None:
        user_input = args.execute
        execute(agent_chain, user_input, index, args.verbose)
    elif args.generate is not None:
        user_input: str = args.generate
        print("Sending query to ChatGPT: " + user_input)
        prompt = construct_generate_prompt(user_input)
        if args.train:
            info = get_doc_content_for_query(index, user_input)
            if info is not None:
                prompt = prompt + info
        response = agent_chain.predict(input=prompt)
        pretty_print(response)
        parsed = extract_code_blocks(response)
        if parsed != []:
            with open("generated.bpf.c", "w") as f:
                for code in parsed:
                    f.write(code)
        else:
            print("It's seems that GPT not generate a ebpf program, what it generate as following:\n{response}")
    else:
        parser.print_help()

def pretty_print(input, lexer=MarkdownLexer, *args, **kwargs) -> None:
    tokens = list(pygments.lex(input, lexer=lexer()))
    print_formatted_text(PygmentsTokens(tokens), *args, **kwargs)

def construct_generate_prompt(text: str) -> str:
    """
    Construct a prompt that generates BPF code.

    :param text: User request.
    :return: Prompt.
    """
    return f"""You are now a translater from human language to {os.uname()[0]} eBPF programs.
Please write eBPF programs for me.
No explanation required, no instruction required, don't tell me how to compile and run.
What I want is just a eBPF program with markdown format for: {text}."""

def construct_running_prompt(text: str) -> str:
    """
    Construct prompts that translate user requests into bpf commands.

    :param text: User request.
    :return: Prompt.
    """
    return f"""You are now a translater from human language to {os.uname()[0]} shell bpftrace command.
No explanation required.
Respond with only the raw shell bpftrace command.
It should be start with `bpftrace`.
Your response should be able to put into a shell and run directly.
Just output in one line, without any description, or any other text that cannot be run in shell.
What should I type to shell to trace using bpftrace for: {text}"""

def get_doc_content_for_query(index: VectorStoreIndex, query: str) -> str:
    """
    Find the content from the document that is closest to the user's request

    :param index: Vector database
    :param query: User's request
    :return: The content that is most relevant to the user's request.
    """
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    related_contents = response.source_nodes
    if related_contents is not None:
        contents = "\nThere are some related information about this query:\n"
        for i, content in enumerate(related_contents):
            info = f"Info {i}: {content.node.get_text()}\n"
            contents += info
        return contents
    else:
        return None

def make_executable_command(command: str) -> str:
    """
    Remove extra characters from the command from the LLM return result

    :param command: The command from the LLM.
    :return: The result of the processing.
    """
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

def init(need_train: bool, verbose: bool) -> list[ConversationChain, VectorStoreIndex]:
    """
    Initialize the conversation and vector database.

    :param need_train: Whether you need to use a vector database.
    :verbose: Whether to print extra information.
    :return agent_chain: A conversation between a human and an AI.
    :return index: Vector database.
    """
    llm = ChatOpenAI(model_name="gpt-3.5-turbo",temperature=0)
    agent_chain = ConversationChain(llm=llm, verbose=verbose,
                    memory=ConversationBufferMemory())
    if need_train:
        if not os.path.exists(f"{LOCAL_PATH}/vector_index/"):
            print(f"{LOCAL_PATH}/vector_index not found. Training...")
            md_files = []
            # Get all markdown files in the tutorial
            for root, _, files in os.walk(DOC_PATH):
                for file in files:
                    if file.endswith('.md'):
                        md_files.append(os.path.join(root, file))
            documents = SimpleDirectoryReader(input_files=md_files).load_data()
            llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003"))
            service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
            index = VectorStoreIndex.from_documents(documents, service_context=service_context)
            index.storage_context.persist(f"{LOCAL_PATH}/vector_index")
            print(f"Training completed, {LOCAL_PATH}/vector_index has been saved.")
        else:
            print(f"Loading the {LOCAL_PATH}/vector_index...")
            storage_context = StorageContext.from_defaults(persist_dir=f"{LOCAL_PATH}/vector_index")
            index = load_index_from_storage(storage_context)
    else:
        index = None
    return agent_chain, index

def execute(agent_chain: ConversationChain, user_input: str, index=None, verbose: bool=False) -> None:
    """
    Convert the user request into a BPF command and execute it.

    :param agent_chain: A conversation between a human and an AI.
    :param user_input: The user's request.
    :param index: Vector database.
    :param verbose: Whether to print extra information.
    """
    print("Sending query to ChatGPT: " + user_input)
    prompt = construct_running_prompt(user_input)
    if index is not None:
        info = get_doc_content_for_query(index, user_input)
        if info is not None:
            prompt = prompt + info
    response = agent_chain.predict(input=prompt)
    parsed = make_executable_command(response)
    print(f"The command generated by gpt is: {parsed}")
    print("Press Ctrl+C to stop the command....")
    ok = False
    stderr_out = tempfile.mktemp()
    for _ in range(5):
        print(f"Get the command from gpt: {parsed}, running...")
        ret_val = os.system(f"sudo {parsed} 2> {stderr_out}")
        if ret_val != 0:
            with open(stderr_out, "r") as f:
                stderr_content = f.read()
            print(f"Failed to run bpftrace with command generated by gpt: {parsed}")
            if verbose:
                print(f"Error message: {stderr_content}\n")
            print("Sending errors to ChatGPT and re-train....\n")
            response = agent_chain.predict(
                input=f"bpftrace gives me the following error on command you generated: `{stderr_content}`, please fix the command according to this error. Remember, just return the command without another information.")
            parsed = make_executable_command(response)
            if verbose:
                print(response)
            if (not parsed.startswith("bpftrace")) or (not parsed.startswith("sudo")):
                continue
        else:
            ok = True
            break
    shutil.rmtree(stderr_out, True)
    if not ok:
        print("Retry times exceeded...")

def extract_code_blocks(text: str) -> list[str]:
    """
    Extract the code block from the returned result.

    :param text: Response result of LLM.
    :return: List of code block.
    """
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

from marko.block import FencedCode
from marko.inline import RawText
from marko.parser import Parser

from gpttrace.utils.prompt import construct_generate_prompt
from gpttrace.utils.common import get_doc_content_for_query, init_conversation, pretty_print


def generate(user_input, need_train, verbose) -> None:
    """
    Convert the user request into a BPF command and execute it.

    :param user_input: The user's request.
    :param need_train: Whether to use the vector database.
    :param verbose: Whether to print extra information.
    """
    agent_chain, index = init_conversation(need_train, verbose)
    print("Sending query to ChatGPT: " + user_input)
    prompt = construct_generate_prompt(user_input)
    if need_train:
        info = get_doc_content_for_query(index, user_input)
        if info is not None:
            prompt = prompt + info
    response = agent_chain.predict(input=prompt)
    pretty_print(response)
    parsed = extract_code_blocks(response)
    if parsed:
        with open("generated.bpf.c", "w", encoding='utf-8') as file:
            for code in parsed:
                file.write(code)
    else:
        print("It's seems that GPT not generate a ebpf program, what it generate as following:\n{response}")

def extract_code_blocks(text: str) -> list[str]:
    """
    Extract the code block from the returned result.

    :param text: Response result of LLM.
    :return: List of code block.
    """
    result = []
    parser = Parser()
    for block in parser.parse(text).children:
        if isinstance(block, FencedCode):
            block: FencedCode
            blk: RawText = block.children[0]
            result.append(blk.children)
    return result

import os
import shutil
import tempfile

from gpttrace.utils.common import get_doc_content_for_query, init_conversation
from gpttrace.prompt import construct_running_prompt, construct_prompt_on_error
from gpttrace.bpftrace import run_bpftrace

def execute(user_input: str, verbose: bool = False, retry: int = 5, previous_prompt: str = None) -> None:
    """
    Convert the user request into a BPF command and execute it.

    :param user_input: The user's request.
    :param need_train: Whether to use the vector database.
    :param verbose: Whether to print extra information.
    """
    if retry == 0:
        print("Retry times exceeded...")
    # agent_chain, index = init_conversation(need_train, verbose)
    # print("Sending query to ChatGPT: " + user_input)
    try:
        if previous_prompt is None:
            prompt = construct_running_prompt(user_input)
        else:
            prompt = construct_prompt_on_error(previous_prompt, user_input, output)
        res = run_bpftrace(prompt, verbose)
        if res["stderr"] != '':
            print("output: " + res)
            print("retry time " + str(retry) + "...")
            # retry
            res = execute(user_input, verbose, retry - 1, prompt)
        else:
            print("AI explanation:")
            
    except Exception as e:
        print("retry time " + str(retry) + " " + str(e))

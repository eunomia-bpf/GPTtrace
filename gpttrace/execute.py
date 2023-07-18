import os
import json
import shutil
import tempfile
import openai

from gpttrace.utils.common import get_doc_content_for_query, init_conversation
from gpttrace.prompt import construct_running_prompt, construct_prompt_on_error, construct_prompt_for_explain
from gpttrace.bpftrace import run_bpftrace


def call_gpt_api(prompt: str) -> str:
    """
    This function sends a list of messages to the GPT model
    """
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
    )
    return response["choices"][0]["message"]["content"]


def execute(user_input: str, verbose: bool = False, retry: int = 5, previous_prompt: str = None, output: str = None) -> None:
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
    if previous_prompt is None:
        prompt = construct_running_prompt(user_input)
    else:
        prompt = construct_prompt_on_error(
            previous_prompt, user_input, output)
    if verbose is True:
        print("Prompt: " + prompt)
    res = run_bpftrace(prompt, verbose)
    if res["stderr"] != '':
        print("output: " + json.dumps(res))
        print("retry time " + str(retry) + "...")
        # retry
        res = execute(user_input, verbose, retry - 1, prompt, json.dumps(res))
    else:
        # success
        print("AI explanation:")
        prompt = construct_prompt_for_explain(user_input, res["stdout"])
        if verbose is True:
            print("Prompt: " + prompt)
        explain = call_gpt_api(prompt)
        print(explain)


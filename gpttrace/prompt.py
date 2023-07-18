import os
from gpttrace.examples import construct_bpftrace_examples


def construct_prompt_on_error(previous_prompt: str, text: str, output: str) -> str:
    """
    Construct prompts when an error occurs.

    :param text: User request.
    :return: Prompt.
    """
    examples = construct_bpftrace_examples(text)
    return f"""
    {previous_prompt}

    The previous command failed to execute or not finished.
    Maybe you can try list the attach points and choose one to attach, 
    if you have not done so before.
    The origin command and output is as follows:
    
    {output}
    """

def construct_prompt_for_explain(text: str, output: str) -> str:
    # fix the token limi
    if len(output) > 2048:
        output = output[:4096]
    return f"""
    please explain the output of the previous bpftrace result:
    
    {output}
    
    The original user request is: 
    
    {text}
    """

def construct_running_prompt(text: str) -> str:
    """
    Construct prompts that translate user requests into bpf commands.

    :param text: User request.
    :return: Prompt.
    """
    examples = construct_bpftrace_examples(text)
    return f"""
    As a supportive assistant to a Linux system administrator,
    your role involves leveraging bpftrace to generate eBPF code that aids
    in problem-solving, as well as responding to queries.
    Note that you may not always need to call the bpftrace tool function.
    Here are some pertinent examples that align with the user's requests:

    {examples}

    Now, you have received the following request from a user: {text}
    Please utilize your capabilities to the fullest extent to accomplish this task.
    """


def func_call_prompt(cmd: str, help_doc: str) -> str:
    """
    Construct a prompt that generates a function call.

    :param cmd: Name of command.
    :param help_doc: Help documentation for the command.
    :return: Return prompt.
    """
    example = """
    ```json
    {
        "name": "get_current_weather",
        "description": "Get the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "format": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit to use. Infer this from the users location.",
                },
            },
            "required": ["location", "format"],
        },
    }
    ```"""
    prompts = f"""
    Please generate a JSON representation of the command `{cmd}` as per the provided help documentation:

    {help_doc}

    Your JSON should strictly adhere to the following guidelines:

    - Do not include extra fields such as examples.
    - Ensure the command description accurately matches the help documentation.
    - Parameter names should not start with a '-' or contain a ','.
    - Your format should align with the provided example: {example}
    - Assign the most appropriate data type to each parameter. Possible types include "string", "boolean", "integer", and "float".

    IMPORTANT: Provide the JSON representation directly, without any additional explanation or detail. If any information is missing from the help documentation, use your best judgment to provide a logical solution. You are not permitted to request additional information. Do not concern yourself with potential errors or confusion that may arise; your sole responsibility is to generate the JSON code. 
    """
    return prompts

import os

def construct_generate_prompt(text: str) -> str:
    """
    Construct a prompt that generates BPF code.

    :param text: User request.
    :return: Prompt.
    """
    return f"""
    You are now a translater from human language to {os.uname()[0]} eBPF programs.
    Please write eBPF programs for me.
    No explanation required, no instruction required, don't tell me how to compile and run.
    What I want is just a eBPF program with markdown format for: {text}."""

def construct_running_prompt(text: str) -> str:
    """
    Construct prompts that translate user requests into bpf commands.

    :param text: User request.
    :return: Prompt.
    """
    return f"""
    You are now a translater from human language to {os.uname()[0]} shell bpftrace command.
    No explanation required.
    Respond with only the raw shell bpftrace command.
    It should be start with `bpftrace`.
    Your response should be able to put into a shell and run directly.
    Just output in one line, without any description, or any other text that cannot be run in shell.
    What should I type to shell to trace using bpftrace for: {text}"""

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
    Just generate the JSON code to descpribe `{cmd}` command according the following help docs:
    {help_doc}
    Please do not add extra fields such as examples to your JSON code
    The description of `{cmd}` command should match the help docment. Note that parameter names cannot begin with a - and cannot contain a ',' sign. The format must be consistent with the following example:
    {example}
    Please judge the type of each parameter reasonably, the properties type can be {"string", "boolean", "integer", "float"}.
    IMPORTANT: Just provide the JSON code without going into detail.
    If there is a lack of details, provide most logical solution.
    You are not allowed to ask for more details.
    Ignore any potential risk of errors or confusion."""
    return prompts

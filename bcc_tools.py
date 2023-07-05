import subprocess
import openai
import json

def bcc_tools(query, verbose):
    # Send the conversation and available functions to GPT
    messages = [{"role": "user", "content": query}]
    functions = get_functions()
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions[:40],
        function_call="auto",
    )
    response_message = response["choices"][0]["message"]
    if verbose:
        print("AI:\n", response)

    if response_message.get("function_call"):
        full_command = ["sudo"]
        cmd = response_message["function_call"]["name"]
        func_descript = get_specify_func(functions, cmd)
        full_command.append(cmd)
        args = json.loads(response_message["function_call"]["arguments"])
        positional_arg = None
        for arg, value in args.items():
            if (value is not True) and (value is not False):
                if not is_positional_arg(cmd, arg):
                    # Determine parameter type
                    arg_type = func_descript["parameters"]["properties"][arg]["type"]
                    if arg_type in ["integer", "float"]:
                        full_command.extend([f"--{arg}",  f'{value}'])
                    else:
                        full_command.extend([f"--{arg}",  f'"{value}"'])
                else:
                    positional_arg = value
            else:
                full_command.append(f"--{arg}")
        if positional_arg is not None:
            full_command.append(positional_arg)
        print("\u001b[1;32m", "Run: ", " ".join(full_command), "\u001b[0m")
        subprocess.run(full_command, text=True)
    else:
        print("LLM does not call any bcc tools.")

def get_functions():
    with open('./funcs.json', 'r') as file:
        data = file.read()
    functions = json.loads(data)
    return functions

def get_specify_func(functions, cmd):
    for func in functions:
        if func.get('name') == cmd:
            return func
    return None

def is_positional_arg(cmd, arg):
    positional_dict = {"profile-bpfcc": "duration", "stackcount-bpfcc": "pattern"}
    if positional_dict.get(cmd) is not None:
        return positional_dict[cmd] == arg
    return False

import subprocess
import openai
import json
from gen_func_call import gen_func_call

def cmd_parser(cmd: str, query: str, verbose=False):
    func_call = None
    functions = get_predifine_funcs()
    for func in functions:
        # Gets the predefined function call
        if func["name"] == cmd:
            func_call= func
            break
    if func_call is None:
        # Generate a function call based on a given command
        func_call = gen_func_call(cmd, verbose)
    messages = [{"role": "user", "content": query}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=[func_call],
        function_call="auto",
    )
    response_message = response["choices"][0]["message"]
    if response_message.get("function_call"):
        cmd_name = response_message["function_call"]["name"]
        args = json.loads(response_message["function_call"]["arguments"])
        func_descript = get_specify_func(functions, cmd_name)
        exec_cmd(cmd_name, args, func_descript)
    else:
        print("LLM does not call any bcc tools.")

def exec_cmd(cmd_name: str, args: str, func_descript: json) -> None:
    """
    Execute the command

    :param cmd_name: The name of the command
    :param args: The parameters required to execute the command.
    :param func_desrcript: The function call description information about the command is in JSON format.
    """
    full_command = ["sudo"]
    full_command.append(cmd_name)
    positional_arg = None
    for arg, value in args.items():
        if (value is not True) and (value is not False):
            if not is_positional_arg(cmd_name, arg):
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
    full_command = [str(item) for item in full_command]
    print("\u001b[1;32m", "Run: ", " ".join(full_command), "\u001b[0m")
    subprocess.run(full_command, text=True, check=True)

def query_suggest_command(functions: json, query: str) -> list:
    # Extract the descriptions of the bcc command
    funcs_info = [func["name"] + ": " + func["description"]  for func in functions]
    funcs_info = "; \n".join(funcs_info)
    prompt = f"""Here is a series of bcc command line tools:
        ```text
        {funcs_info}
        ```
        Please directly return a collection of command names (up to a maximum of 10 commands) **that you believe are most likely to solve the problem: "{query}"**. 
        If there is a lack of details, provide most logical solution.
        IMPORT: The returned result should follow the following format:
        [opensnoop-bpfcc, stackcount-bpfcc, tclstat-bpfcc]
    """

    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    response_message = response["choices"][0]["message"]
    funcs_suggest = response_message["content"][1:-1].split(", ")
    return funcs_suggest

def get_predifine_funcs():
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
    positional_dict = {
        "biolatency-bpfcc": ["interval", "count"],
        "biotop-bpfcc": ["interval", "count"],
        "btrfsdist-bpfcc": ["interval", "count"],
        "btrfsslower-bpfcc": ["min_ms"],
        "cachestat-bpfcc": ["interval", "count"],
        "cachetop-bpfcc": ["interval"],
        "cpudist-bpfcc": ["interval", "count"],
        "cpuunclaimed-bpfcc": ["interval", "count"],
        "dbslower-bpfcc": ["engine"],
        "dbstat-bpfcc": ["engine"],
        "deadlock-bpfcc": ["pid"],
        "ext4dist-bpfcc": ["interval", "count"],
        "ext4slower-bpfcc": ["min_ms"],
        "fileslower-bpfcc": ["min_ms"],
        "filetop-bpfcc": ["interval", "count"],
        "funccount-bpfcc": ["pattern"],
        "funclatency-bpfcc": ["pattern"],
        "funcslower-bpfcc": ["function"],
        "hardirqs-bpfcc": ["interval", "outputs"],
        "inject-bpfcc": ["base_function", "spec"],
        "llcstat-bpfcc": ["duration"],
        "memleak-bpfcc": ["interval", "count"],
        "nfsdist-bpfcc": ["interval", "count"],
        "nfsslower-bpfcc": ["min_ms"],
        "offcputime-bpfcc": ["duration"],
        "offwaketime-bpfcc": ["duration"],
        "profile-bpfcc": ["duration"],
        "runqlat-bpfcc": ["interval", "count"],
        "runqlen-bpfcc": ["interval", "count"],
        "runqslower-bpfcc": ["min_us"],
        "slabratetop-bpfcc": ["interval", "count"],
        "softirqs-bpfcc": ["interval", "count"],
        "stackcount-bpfcc": ["pattern"],
        "tcpconnlat-bpfcc": ["duration_ms"],
        "tcpsubnet-bpfcc": ["subnets"],
        "tcptop-bpfcc": ["interval", "count"],
        "tplist-bpfcc": ["filter"],
        "trace-bpfcc": ["probe"],
        "ttysnoop-bpfcc": ["device"],
        "ucalls": ["pid", "interval"],
        "uflow": ["pid"],
        "ugc": ["pid"],
        "uobjnew": ["pid", "interval"],
        "ustat": ["interval", "count"],
        "uthreads": ["pid"],
        "wakeuptime-bpfcc": ["duration"],
        "xfsdist-bpfcc": ["interval", "count"],
        "xfsslower-bpfcc": ["min_ms"],
        "zfsdist-bpfcc": ["interval", "count"],
        "zfsslower-bpfcc": ["min_ms"],
        "dcstat-bpfcc": ["interval", "count"]
    }

    if positional_dict.get(cmd) is not None:
        return arg in positional_dict[cmd]
    return False

if __name__ == "__main__":
    cmd_parser("print 1 second summaries, 10 times", True)

import subprocess
import openai
import json

from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from gpttrace.prompt import func_call_prompt
from gpttrace.config import cfg

def cmd(cmd_name: str, query: str, verbose=False) -> None:
    """
    Generate the command based on query and execute the command.

    :param cmd_name: name of command.
    :param query: The task that the user wants to accomplish with `cmd`.
    :param verbose: Whether to print extra information.
    """
    func_call = None
    functions = get_predifine_funcs()
    for func in functions:
        # Gets the predefined function call
        if func["name"] == cmd_name:
            func_call = func
            break
    if func_call is None:
        # Generate a function call based on a given command
        func_call = gen_func_call(cmd_name, verbose)
    messages = [{"role": "user", "content": query}]
    response = openai.ChatCompletion.create(
        model=cfg.get("DEFAULT_MODEL"),
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
    try:
        subprocess.run(full_command, text=True, check=True)
    except subprocess.CalledProcessError as err:
        print("\u001b[1;31m\bFailed to execute command!\u001b[0m")
        print(err)

def get_predifine_funcs() -> str:
    """
    Gets the JSON format description information of the predefined function call.

    :return: List of JSON-formatted function calls.
    """
    func_path = cfg.get("BCC_FUNC_CALL_PATH")
    with open(func_path, 'r', encoding='utf-8') as file:
        data = file.read()
    functions = json.loads(data)
    return functions

def gen_func_call(cmd_name: str, verbose: bool) -> str:
    """
    Generates a funciton call for the given command.

    :param cmd_name: Name of command.
    :verbose: Whether to print extra information.
    :return: The function call in JSON format corresponding to the command.
    """
    model_name = cfg.get("DEFAULT_MODEL")
    llm = ChatOpenAI(model=model_name,temperature=0)
    agent_chain = ConversationChain(llm=llm, verbose=verbose,
                    memory=ConversationBufferMemory())
    help_doc = get_command_help(cmd_name)
    prompt = func_call_prompt(cmd_name, help_doc)
    response = agent_chain.predict(input=prompt)
    return response

def get_command_help(command) -> str:
    """
    Gets help documentation for the command.

    :param command: Name of command.
    :return: Help documentation for the command.
    """
    try:
        output = subprocess.check_output([command, '--help'], universal_newlines=True)
        return output
    except subprocess.CalledProcessError as err:
        return f"Error executing help command: {err.output}"

def get_specify_func(functions, cmd_name) -> json:
    """
    Gets the JSON format description of the function call for the specified command.

    :param functions: A predefined list of function calls.
    :param cmd_name: A specific command.
    :return func: The function call corresponding to cmd.
    """
    for func in functions:
        if func.get('name') == cmd_name:
            return func
    return None


def is_positional_arg(cmd_name, arg) -> bool:
    """
    Determine if the argument passed to the command is a position argument.

    :param cmd_name: name of command.
    :param arg: argument passed to command.
    :return: Whether arg is a positional parameter of cmd.
    """

    positional_dict = {
        "biolatency-bpfcc": ["interval", "count"],
        "biotop-bpfcc": ["interval", "count"],
        "btrfsdist-bpfcc": ["interval", "count"],
        "btrfsslower-bpfcc": ["min_ms"],
        "cachestat-bpfcc": ["interval", "count"],
        "cachetop-bpfcc": ["interval"],
        "cobjnew-bpfcc": ["pid", "interval"],
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
        "javacalls-bpfcc": ["pid", "interval"],
        "javaflow-bpfcc": ["pid"],
        "javagc-bpfcc": ["pid"],
        "javaobjnew-bpfcc": ["pid", "interval"],
        "javastat-bpfcc": ["interval", "count"],
        "javathreads-bpfcc": ["pid"],
        "llcstat-bpfcc": ["duration"],
        "memleak-bpfcc": ["interval", "count"],
        "nfsdist-bpfcc": ["interval", "count"],
        "nfsslower-bpfcc": ["min_ms"],
        "nodegc-bpfcc": ["pid"],
        "nodestat-bpfcc": ["interval", "count"],
        "offcputime-bpfcc": ["duration"],
        "offwaketime-bpfcc": ["duration"],
        "perlcalls-bpfcc": ["pid", "interval"],
        "perlflow-bpfcc": ["pid"],
        "perlstat-bpfcc": ["interval", "count"],
        "phpcalls-bpfcc": ["pid", "interval"],
        "phpflow-bpfcc": ["pid"],
        "phpstat-bpfcc": ["interval", "count"],
        "profile-bpfcc": ["duration"],
        "pythoncalls-bpfcc": ["pid", "interval"],
        "pythonflow-bpfcc": ["pid"],
        "pythongc-bpfcc": ["pid"],
        "pythonstat-bpfcc": ["interval", "count"],
        "rubycalls-bpfcc": ["pid", "interval"],
        "rubyflow-bpfcc": ["pid"],
        "rubygc-bpfcc": ["pid"],
        "rubyobjnew-bpfcc": ["pid", "interval"],
        "rubystat-bpfcc": ["interval", "count"],
        "runqlat-bpfcc": ["interval", "count"],
        "runqlen-bpfcc": ["interval", "count"],
        "runqslower-bpfcc": ["min_us"],
        "slabratetop-bpfcc": ["interval", "count"],
        "softirqs-bpfcc": ["interval", "count"],
        "stackcount-bpfcc": ["pattern"],
        "tclcalls-bpfcc": ["pid", "interval"],
        "tclflow-bpfcc": ["pid"],
        "tclobjnew-bpfcc": ["pid", "interval"],
        "tclstat-bpfcc": ["interval", "count"],
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
    }

    if positional_dict.get(cmd_name) is not None:
        return arg in positional_dict[cmd]
    return False

if __name__ == "__main__":
    cmd("print 1 second summaries, 10 times", True)

#!/bin/python
import subprocess
import openai
import json
import unittest
import threading

functions = [
    {
        "name": "bpftrace",
        "description": "A high-level tracing language for Linux enhanced Berkeley Packet Filter (eBPF)",
        "parameters": {
            "type": "object",
            "properties": {
                "bufferingMode": {
                    "type": "string",
                    "description": "output buffering mode"
                },
                "format": {
                    "type": "string",
                    "description": "output format"
                },
                "outputFile": {
                    "type": "string",
                    "description": "redirect bpftrace output to file"
                },
                "debugInfo": {
                    "type": "boolean",
                    "description": "debug info dry run"
                },
                "verboseDebugInfo": {
                    "type": "boolean",
                    "description": "verbose debug info dry run"
                },
                "program": {
                    "type": "string",
                    "description": "program to execute"
                },
                "includeDir": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "directories to add to the include search path"
                },
                "usdtFileActivation": {
                    "type": "boolean",
                    "description": "activate usdt semaphores based on file path"
                },
                "unsafe": {
                    "type": "boolean",
                    "description": "allow unsafe builtin functions"
                },
                "quiet": {
                    "type": "boolean",
                    "description": "keep messages quiet"
                },
                "verbose": {
                    "type": "boolean",
                    "description": "verbose messages"
                },
                "noWarnings": {
                    "type": "boolean",
                    "description": "disable all warning messages"
                },
                "timeout": {
                    "type": "integer",
                    "description": "seconds to run the command"
                },
                "continue": {
                    "type": "boolean",
                    "description": "finish conversation and not continue."
                }
            },
            "required": ["program"]
        }

    }
]


def run_command_with_timeout(command, timeout: str):
    print("The bpf program to run is: " + ' '.join(command))
    print("timeout: " + str(timeout))
    user_input = input("Enter 'y' to proceed: ")
    if user_input.lower() != 'y':
        print("Aborting...")
        exit()
    # Start the process
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
        timer = threading.Timer(timeout, process.kill)
        try:
            # Set a timer to kill the process if it doesn't finish within the timeout
            timer.start()
            accept_stdout = ""
            while process.poll() is None:
                # Only try to read output if the process is still running
                if process.stdout.readable():
                    line = process.stdout.read()
                    print(line, end='')
                    accept_stdout += line
            # Wait for the process to finish and get the output
            stdout, stderr = process.communicate()
        except Exception as e:
            print("Exception: " + str(e))
        finally:
            # Make sure the timer is canceled
            timer.cancel()
            return {
                "command": ' '.join(command),
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode
            }

def construct_command(operation):
    cmd = []
    if "bufferingMode" in operation:
        cmd += ["-B", operation["bufferingMode"]]
    if "format" in operation:
        cmd += ["-f", operation["format"]]
    if "outputFile" in operation:
        cmd += ["-o", operation["outputFile"]]
    if "debugInfo" in operation and operation["debugInfo"]:
        cmd += ["-d"]
    if "verboseDebugInfo" in operation and operation["verboseDebugInfo"]:
        cmd += ["-dd"]
    if "program" in operation:
        cmd += ["-e", operation["program"]]
    if "includeDir" in operation:
        for dir in operation["includeDir"]:
            cmd += ["-I", dir]
    if "usdtFileActivation" in operation and operation["usdtFileActivation"]:
        cmd += ["--usdt-file-activation"]
    if "unsafe" in operation and operation["unsafe"]:
        cmd += ["--unsafe"]
    if "quiet" in operation and operation["quiet"]:
        cmd += ["-q"]
    if "verbose" in operation and operation["verbose"]:
        cmd += ["-v"]
    if "noWarnings" in operation and operation["noWarnings"]:
        cmd += ["--no-warnings"]
    # ...add other options similarly...
    return cmd

def run_bpftrace(prompt: str, verbose: bool = False) -> object:
    """
    This function sends a list of messages and functions to the GPT model
    and runs the function call returned by the model.

    Parameters:
    messages (list): A list of dictionaries where each dictionary represents a message.

    Returns:
    None
    """
    # Send the conversation and available functions to GPT
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=functions,
        function_call="auto",  # auto is default, but we'll be explicit
    )
    response_message = response["choices"][0]["message"]
    if verbose:
        print(response_message)
    # Check if GPT wanted to call a function
    if response_message.get("function_call"):
        full_command = ["sudo"]
        full_command.append(response_message["function_call"]["name"])
        args = json.loads(response_message["function_call"]["arguments"])

        command = construct_command(args)
        full_command.extend(command)
        timeout = 20  # default is running for 20 seconds
        if args.get("timeout"):
            timeout = args["timeout"]
        res = run_command_with_timeout(full_command, timeout)
        if args.get("continue") and res["stderr"] == "":
            # continue conversation
            res["stderr"] = "The conversation shall not complete."
        return res
    else:
        return response_message


class TestRunBpftrace(unittest.TestCase):
    def test_summary(self):
        res = run_bpftrace("tracing with Count page faults by process")
        print(res)
        print(res["stderr"])

    def test_construct_command(self):
        operation_json = """
        {
            "bufferingMode": "full",
            "format": "json",
            "outputFile": "output.txt",
            "program": "kprobe:do_nanosleep { printf(\\"PID %d sleeping...\\n\\", pid); }",
            "includeDir": ["dir1", "dir2"]
        }
        """

        operation = json.loads(operation_json)
        command = construct_command(operation)
        print(command)

    def test_construct_complex_command(self):
        operation_json = """
        {
            "bufferingMode": "full",
            "format": "json",
            "outputFile": "output.txt",
            "debugInfo": true,
            "verboseDebugInfo": true,
            "program": "kprobe:do_nanosleep { printf(\\"PID %d sleeping...\\n\\", pid); }",
            "includeDir": ["dir1", "dir2"],
            "usdtFileActivation": true,
            "unsafe": true,
            "quiet": true,
            "verbose": true,
            "noWarnings": true
        }
        """

        operation = json.loads(operation_json)
        command = construct_command(operation)
        print(command)
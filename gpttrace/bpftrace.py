"""BPFtrace integration module for GPTtrace."""
#!/bin/python
import json
import subprocess
import sys
import threading
import unittest
from typing import Any, Dict, List, TypedDict

import openai

functions = [
    {
        "name": "bpftrace",
        "description": "A tool use to run bpftrace eBPF programs",
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
    },
    {
        "name": "SaveFile",
        "description": "Save the eBPF program to file",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "the file name to save to"
                },
                "content": {
                    "type": "string",
                    "description": "the file content"
                }
            },
            "required": ["filename", "content"]
        }
    }
]

class CommandResult(TypedDict):
    """Type definition for command execution results."""
    command: str
    stdout: str
    stderr: str
    returncode: int

def run_command_with_timeout(command: List[str], timeout: int) -> CommandResult:
    """
    This function runs a command with a timeout.
    """
    print("The bpf program to run is: " + ' '.join(command))
    print("timeout: " + str(timeout))
    user_input = input("Enter 'y' to proceed: ")
    if user_input.lower() != 'y':
        print("Aborting...")
        sys.exit(1)
    # Start the process
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True) as process:
        timer = threading.Timer(timeout, process.kill)
        stdout = ""
        stderr = ""
        returncode = -1
        try:
            # Set a timer to kill the process if it doesn't finish within the timeout
            timer.start()
            while process.poll() is None:
                # Only try to read output if the process is still running
                if process.stdout.readable():
                    line = process.stdout.read()
                    print(line, end='')
                    stdout += line
            # Wait for the process to finish and get the output
            last_stdout, last_stderr = process.communicate()
            stdout += last_stdout
            stderr += last_stderr
            returncode = process.returncode
        except (OSError, ValueError) as err:
            print("Exception: " + str(err))
        finally:
            # Make sure the timer is canceled
            timer.cancel()
            if process.poll() is None and process.stdout.readable():
                stdout += process.stdout.read()
                print(stdout)
            if process.poll() is None and process.stderr.readable():
                stderr += process.stderr.read()
                print(stderr)
            # Ensure returncode is set even if there was an exception
            if returncode is None and process.poll() is not None:
                returncode = process.returncode
        return {
            "command": ' '.join(command),
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }


def construct_command(operation: Dict[str, Any]) -> List[str]:
    """
    This function constructs a command from a dictionary of options.
    """
    cmd: List[str] = []
    value_flags = (
        ("bufferingMode", "-B"),
        ("format", "-f"),
        ("outputFile", "-o"),
        ("program", "-e"),
    )
    bool_flags = (
        ("debugInfo", "-d"),
        ("verboseDebugInfo", "-dd"),
        ("usdtFileActivation", "--usdt-file-activation"),
        ("unsafe", "--unsafe"),
        ("quiet", "-q"),
        ("verbose", "-v"),
        ("noWarnings", "--no-warnings"),
    )

    for option_name, flag in value_flags:
        if option_name in operation:
            cmd.extend([flag, operation[option_name]])

    for include_dir in operation.get("includeDir", []):
        cmd.extend(["-I", include_dir])

    for option_name, flag in bool_flags:
        if operation.get(option_name):
            cmd.append(flag)

    # ...add other options similarly...
    return cmd


def run_bpftrace(prompt: str, verbose: bool = False) -> CommandResult:
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
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        function_call="auto",  # auto is default, but we'll be explicit
    )
    response_message = response["choices"][0]["message"]
    if verbose:
        print(response_message)
    # Check if GPT wanted to call a function
    if not response_message.get("function_call"):
        # not function call
        return {
            "command": "response_message",
            "stdout": response_message["content"],
            "stderr": "",
            "returncode": 0
        }

    function_call = response_message["function_call"]
    function_name = function_call["name"]
    args = json.loads(function_call["arguments"])

    if function_name == "bpftrace":
        full_command = ["sudo", function_name]
        command = construct_command(args)
        full_command.extend(command)
        timeout = int(args.get("timeout", 300))
        # run the bpftrace command
        res = run_command_with_timeout(full_command, timeout)
        if args.get("continue") and res["stderr"] == "":
            # continue conversation
            res["stderr"] = "The conversation shall not complete."
        return res

    if function_name == "SaveFile":
        filename = args["filename"]
        print("Save to file: " + filename)
        print(args["content"])
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(args["content"])
        return {
            "command": "SaveFile",
            "stdout": args["content"],
            "stderr": "",
            "returncode": 0
        }

    return {
        "command": function_name,
        "stdout": "",
        "stderr": f"Unsupported function call: {function_name}",
        "returncode": 1
    }


class TestRunBpftrace(unittest.TestCase):
    """Test cases for bpftrace integration."""

    def test_summary(self):
        """Test running bpftrace with a summary request."""
        res = run_bpftrace("tracing with Count page faults by process for 3s")
        print(res)
        print(res["stderr"])

    def test_construct_command(self):
        """Test construction of bpftrace commands."""
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
        """Test construction of complex bpftrace commands."""
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

    def test_run_command_with_timeout_short_live(self):
        """Test running a short-lived command with timeout."""
        command = ["ls", "-l"]
        timeout = 5
        result = run_command_with_timeout(command, timeout)
        print(result)
        self.assertNotEqual(result["stdout"], "")
        self.assertEqual(result["command"], "ls -l")
        self.assertEqual(result["returncode"], 0)

import subprocess

from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain


def gen_func_call(cmd: str, verbose: bool):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo",temperature=0)
    agent_chain = ConversationChain(llm=llm, verbose=verbose,
                    memory=ConversationBufferMemory())
    help_doc = get_command_help(cmd)
    prompt = construct_generate_prompt(cmd, help_doc)
    # print("Sending query to ChatGPT:\n\n" + prompt + "\n\n")
    response = agent_chain.predict(input=prompt)
    return response

def get_command_help(command):
    try:
        output = subprocess.check_output([command, '--help'], universal_newlines=True)
        return output
    except subprocess.CalledProcessError as e:
        return f"Error executing help command: {e.output}"

def construct_generate_prompt(cmd: str, help_doc: str) -> str:
    example = """```json
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

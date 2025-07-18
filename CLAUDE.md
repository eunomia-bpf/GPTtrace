# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Install Dependencies
```bash
pip install -r requirements.txt
# or for development install
pip install -e .
```

### Run the Application
```bash
# Direct execution
python3 -m gpttrace "Your eBPF program request"

# With OpenAI API key
python3 -m gpttrace -k YOUR_API_KEY "Count page faults by process"

# Use bcc tool for tracing
python3 -m gpttrace -c CMD_NAME "Your query"

# Verbose mode
python3 -m gpttrace -v "Your request"
```

### Linting and Code Quality
```bash
# Run pylint (currently commented out in CI)
pylint $(git ls-files '*.py')

# Run ruff for linting (configured in pyproject.toml)
ruff check .

# Run mypy for type checking
mypy gpttrace

# Run code formatting with black and isort
black gpttrace
isort gpttrace
```

### Building and Publishing
```bash
# Build the package
python -m build

# Install locally in development mode
pip install -e .
```

## Code Architecture

### Core Components

1. **gpttrace/GPTtrace.py**: Main entry point that handles CLI argument parsing and routes to either `cmd` or `execute` functions

2. **gpttrace/execute.py**: Core execution logic that:
   - Calls GPT API (OpenAI or LiteLLM) to generate eBPF programs
   - Handles retries on failures
   - Integrates with vector database for examples
   - Manages the prompt construction and error handling

3. **gpttrace/bpftrace.py**: bpftrace integration that:
   - Defines OpenAI function calling schema for bpftrace parameters
   - Executes bpftrace programs with proper argument handling
   - Manages subprocess execution and output capture

4. **gpttrace/cmd.py**: Handles bcc tool command execution for pre-built tracing tools

5. **gpttrace/prompt.py**: Prompt engineering functions for:
   - Constructing initial prompts with system info and examples
   - Building error correction prompts
   - Creating explanation prompts for results

6. **gpttrace/utils/common.py**: Utility functions for:
   - Vector database queries
   - Pretty printing results
   - Conversation initialization

### Data and Examples

- **tools/**: Contains bpftrace example scripts (*.bt) and their corresponding output examples (*_example.txt)
- **data_save/funcs.json**: Pre-built function descriptions for vector search
- **tools/examples.json**: Mapping of natural language queries to example scripts

### Key Design Patterns

1. **Retry Mechanism**: The system retries up to 5 times when eBPF programs fail to load, using error messages to improve the prompt

2. **Vector Search**: Uses llama_index to search for relevant eBPF program examples based on user queries

3. **Function Calling**: Leverages OpenAI's function calling API to structure bpftrace program generation

4. **Two Execution Modes**:
   - Direct eBPF program generation via `execute()`
   - Pre-built bcc tool selection via `cmd()`

## Environment Requirements

- Python >= 3.6
- OpenAI API key (via OPENAI_API_KEY environment variable or -k parameter)
- Linux system with eBPF support
- bpftrace installed for eBPF program execution
- bcc tools installed for pre-built tracing commands
# GPTtrace 🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Actions Status](https://github.com/eunomia-bpf/GPTtrace/workflows/Pylint/badge.svg)](https://github.com/eunomia-bpf/GPTtrace/actions)
[![DeepSource](https://deepsource.io/gh/eunomia-bpf/eunomia-bpf.svg/?label=active+issues&show_trend=true&token=rcSI3J1-gpwLIgZWtKZC-N6C)](https://deepsource.io/gh/eunomia-bpf/eunomia-bpf/?ref=repository-badge)
[![CodeFactor](https://www.codefactor.io/repository/github/eunomia-bpf/eunomia-bpf/badge)](https://www.codefactor.io/repository/github/eunomia-bpf/eunomia-bpf)


Generate eBPF programs and tracing with ChatGPT and natural language

## Key Features 💡

### Interact and Tracing your Linux with natural language, it can tell how to write eBPF programs in `BCC`, `libbpf` styles.

example: tracing with Count page faults by process

![result](doc/result.gif)

### Generate eBPF programs with natural language

![generate](doc/generate.png)

For detail documents and tutorials about how we train ChatGPT to write eBPF programs, please refer to:  [`https://github.com/eunomia-bpf/bpf-developer-tutorial`](https://github.com/eunomia-bpf/bpf-developer-tutorial) （基于 CO-RE (一次编写，到处运行） libbpf 的 eBPF 开发者教程：通过 20 个小工具一步步学习 eBPF（尝试教会 ChatGPT 编写 eBPF 程序）

## Usage and Setup 🛠

```console
$ ./GPTtrace.py
usage: GPTtrace [-h] [-i | -v | -e TEXT | -g TEXT] [-u UUID] [-t ACCESS_TOKEN]

Use ChatGPT to write eBPF programs (bpftrace, etc.)

optional arguments:
  -h, --help            show this help message and exit
  -i, --info            Let ChatGPT explain what's eBPF
  -v, --verbose         Print the prompt and receive message
  -e TEXT, --execute TEXT
                        Generate commands using your input with ChatGPT, and run it
  -g TEXT, --generate TEXT
                        Generate eBPF programs using your input with ChatGPT
  -u UUID, --uuid UUID  Conversion UUID to use, or passed through environment variable `GPTTRACE_CONV_UUID`
  -t ACCESS_TOKEN, --access-token ACCESS_TOKEN
                        ChatGPT access token, see `https://chat.openai.com/api/auth/session` or passed through
                        `GPTTRACE_ACCESS_TOKEN`
```

### First: login to ChatGPT

- get the `Conversion ID` from ChatGPT, and then set it to the environment variable `GPTTRACE_CONV_UUID` or use the `-u` option. The `Conversion ID` is the last part of the URL of the conversation, for example, the `Conversion ID` of `https://chat.openai.com/conv/1a2b3c4d-0000-0000-0000-1k2l3m4n5o6p` is `1a2b3c4d-0000-0000-0000-1k2l3m4n5o6p`(example, not usable).
- get the `access token` from ChatGPT, and then set it to the environment variable `GPTTRACE_ACCESS_TOKEN` or use the `-t` option. see `https://chat.openai.com/api/auth/session` for the access token.

### Use prompts to teach ChatGPT to write eBPF programs

```sh
./GPTtrace.py -t
```

This will use the material in the `prompts` directory to teach ChatGPT to write eBPF programs in bpftrace, libbpf, and BCC styles. You can also do that manually by sending the prompts to ChatGPT in the Website.

### start your tracing! 🚀

For example:

```sh
./GPTtrace.py -e "Count page faults by process"
```

## Installation 🔧

```sh
./install.sh
```

## Examples

- Files opened by process
- Syscall count by program
- Read bytes by process:
- Read size distribution by process:
- Show per-second syscall rates:
- Trace disk size by process
- Count page faults by process
- Count LLC cache misses by process name and PID (uses PMCs):
- Profile user-level stacks at 99 Hertz, for PID 189:
- Files opened, for processes in the root cgroup-v2

## LICENSE

MIT

## 🔗 Links

- detail documents and tutorials about how we train ChatGPT to write eBPF programs: https://github.com/eunomia-bpf/bpf-developer-tutorial （基于 CO-RE (一次编写，到处运行） libbpf 的 eBPF 开发者教程：通过 20 个小工具一步步学习 eBPF（尝试教会 ChatGPT 编写 eBPF 程序）
- bpftrace: https://github.com/iovisor/bpftrace
- ChatGPT: https://chat.openai.com/

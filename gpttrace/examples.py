import os
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.vectorstores import DocArrayInMemorySearch
# from langchain.document_loaders import DirectoryLoader

# loader = DirectoryLoader('gpttrace/tools/', glob="**/*.bt")
# docs = loader.load()
# embeddings = OpenAIEmbeddings()

# db = DocArrayInMemorySearch.from_documents(docs, embeddings)

simple_examples = """
# list probes containing "sleep"
bpftrace -l '*sleep*'

# trace processes calling sleep
bpftrace -e 'kprobe:do_nanosleep { printf("PID %d sleeping...\n", pid); }'

# count syscalls by process name
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# Files opened by process
bpftrace -e 'tracepoint:syscalls:sys_enter_open { printf("%s %s\n", comm, str(args->filename)); }'

# Syscall count by program
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# Read bytes by process:
bpftrace -e 'tracepoint:syscalls:sys_exit_read /args->ret/ { @[comm] = sum(args->ret); }'

# Read size distribution by process:
bpftrace -e 'tracepoint:syscalls:sys_exit_read { @[comm] = hist(args->ret); }'

# Show per-second syscall rates:
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @ = count(); } interval:s:1 { print(@); clear(@); }'

# Trace disk size by process
bpftrace -e 'tracepoint:block:block_rq_issue { printf("%d %s %d\n", pid, comm, args->bytes); }'

# Count page faults by process
bpftrace -e 'software:faults:1 { @[comm] = count(); }'

# Count LLC cache misses by process name and PID (uses PMCs):
bpftrace -e 'hardware:cache-misses:1000000 { @[comm, pid] = count(); }'

# Profile user-level stacks at 99 Hertz, for PID 189:
bpftrace -e 'profile:hz:99 /pid == 189/ { @[ustack] = count(); }'

# Files opened, for processes in the root cgroup-v2
bpftrace -e 'tracepoint:syscalls:sys_enter_openat /cgroup == cgroupid("/sys/fs/cgroup/unified/mycg")/ { printf("%s\n", str(args->filename)); }'

"""

def get_bpftrace_basic_examples(text: str) -> str:
    return simple_examples

def construct_bpftrace_examples(text: str) -> str:
    examples = get_bpftrace_basic_examples(text)
    # docs = db.similarity_search(text)
    # examples += "\n The following is a more complex example: \n"
    # examples += docs[0].page_content
    return examples
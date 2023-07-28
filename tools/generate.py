import openai
import os
import json
import glob
import time
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_bpf_summary(bpf_code):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": 
                f"""
Given this BPF code:

{bpf_code}

Provide a concise and clear summary in one or two sentences. 
Frame the explanation as a user's request to a developer to write a BPF code. 
Avoid beginning with phrases like 'This BPF code is...' Instead, 
start with action-oriented phrases such as 'Write a BPF code that...'
"""
                
                
                }
        ],
        max_tokens=1500
    )

    output = response.choices[0].message['content']
    return output


def get_all_bpf_in_dir(directory):
    all_files = glob.glob(directory + '/*.bt')
    all_bpf = []
    for file in all_files:
        print("opening file: " + file)
        # sleep for a short time to avoid hitting the rate limit
        # Sleep for 5 seconds
        time.sleep(3)
        with open(file, 'r') as f:
            bpf_code = f.read()
            summary = get_bpf_summary(bpf_code)
            all_bpf.append({
                "request": summary,
                "bpf": bpf_code
            })
            print(bpf_code)
            print(summary)
            
    return all_bpf


directory = './'
all_bpf = get_all_bpf_in_dir(directory)
with open('output.json', 'w') as outfile:
    json.dump(all_bpf, outfile)

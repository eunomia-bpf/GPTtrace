import re
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

def write_example_to_json():
    directory = './'
    all_bpf = get_all_bpf_in_dir(directory)
    with open('output.json', 'w') as outfile:
        json.dump(all_bpf, outfile)

def remove_multiline_comments(lines):
    """
    Remove multiline comments from a list of lines.

    This function takes a list of lines as input and removes multiline comments
    that start with '/*' and end with '*/'. The function returns the cleaned
    content without the multiline comments.
    """

    inside_comment = False
    cleaned_lines = []

    for line in lines:
        if not inside_comment:
            start_index = line.find('/*')
            end_index = line.find('*/', start_index + 2)
            
            if start_index != -1 and end_index != -1:
                inside_comment = False
                cleaned_line = line[:start_index] + line[end_index + 2:]
                cleaned_lines.append(cleaned_line)
            elif start_index != -1:
                inside_comment = True
                cleaned_line = line[:start_index]
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)
        else:
            end_index = line.find('*/')
            if end_index != -1:
                inside_comment = False
                cleaned_line = line[end_index + 2:]
                cleaned_lines.append(cleaned_line)

    cleaned_content = ''.join(cleaned_lines)
    return cleaned_content

def reformat():
    rearranged_data = {"data": []}
    with open("./tools/output.json", mode='r', encoding='utf-8') as file:
        contents = json.load(file)
        for content in contents:
            cleaned_content = remove_multiline_comments(re.split(r'(\n)', content['bpf']))
            example = f"example: {content['request']}\n\n```\n{cleaned_content}\n```\n"
            info = {"content": example}
            rearranged_data["data"].append(info)

    with open("./tools/examples.json", 'w', encoding='utf-8') as file:
        json.dump(rearranged_data, file)
    
if __name__ == "__main__":
    reformat()

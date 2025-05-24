import os
import json
import sys

import dotenv
import argparse
from datetime import datetime, timedelta

import langchain_core.exceptions
from langchain_openai import ChatOpenAI
from langchain.prompts import (
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
  HumanMessagePromptTemplate,
)
from structure import Structure
if os.path.exists('.env'):
    dotenv.load_dotenv()
template = open("template.txt", "r").read()
system = open("system.txt", "r").read()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="jsonline data file")
    return parser.parse_args()

def get_yestoday(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    # 计算昨天
    yesterday = date_obj - timedelta(days=1)
    # 转换为字符串
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    return yesterday_str


def main():
    args = parse_args()
    model_name = os.environ.get("MODEL_NAME", 'deepseek-chat')
    language = os.environ.get("LANGUAGE", 'Chinese')
    interests = '''
1. Large Language Models (LLMs) 
1) general-purpose LLM training and inference
2) Evaluation and benchmarking
3) Interpretability and analysis
4) Reinforcement learning (e.g., RLHF)
5) Trustworthy AI (robustness, fairness, safety)

2. Foundation Model Architectures
1) Transformer optimization and variants
2) State space models (e.g., Mamba)
3) Efficient and scalable architecture design
'''
    interests = os.environ.get("INTERESTS", interests)

    data = []
    with open(args.data, "r") as f:
        for line in f:
            data.append(json.loads(line))
    
    seen_ids = set()

    date_today = get_yestoday(os.path.basename(args.data).replace(".jsonl", ""))
    for _ in range(3):
        path = os.path.join(os.path.dirname(args.data), date_today + ".jsonl")
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    item = json.loads(line)
                    seen_ids.add(item['id'])
        date_today = get_yestoday(date_today)
    
    unique_data = []
    for item in data:
        if item['id'] not in seen_ids:
            seen_ids.add(item['id'])
            unique_data.append(item)

    data = unique_data

    print('Open:', args.data, file=sys.stderr)

    llm = ChatOpenAI(model=model_name).with_structured_output(Structure, method="function_calling")
    print('Connect to:', model_name, file=sys.stderr)
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system),
        HumanMessagePromptTemplate.from_template(template=template)
    ])

    chain = prompt_template | llm

    for idx, d in enumerate(data):
        try:
            response: Structure = chain.invoke({
                "language": language,
                "content": d['summary'],
                "interests": interests
            })
            d['AI'] = response.model_dump()
        except langchain_core.exceptions.OutputParserException as e:
            print(f"{d['id']} has an error: {e}", file=sys.stderr)
            d['AI'] = {
                 "tldr": "Error",
                 "motivation": "Error",
                 "method": "Error",
                 "result": "Error",
                 "conclusion": "Error",
                 "relevance": 1.0
            }
        with open(args.data.replace('.jsonl', f'_AI_enhanced_{language}.jsonl'), "a") as f:
            f.write(json.dumps(d) + "\n")

        print(f"Finished {idx+1}/{len(data)}", file=sys.stderr)

if __name__ == "__main__":
    main()

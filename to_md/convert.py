import json
import argparse
import os
from itertools import count

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, help="Path to the jsonline file")
    args = parser.parse_args()
    data = []
    preference = os.environ.get('CATEGORIES', 'cs.CV, cs.CL').split(',')
    preference = list(map(lambda x: x.strip(), preference))
    def rank(cate):
        if cate in preference:
            return preference.index(cate)
        else:
            return len(preference)
    
    def get_right_cate(cate_list):
        for c in cate_list:
            if c in preference:
                return c
        return cate_list[0]
    
    if not os.path.exists(args.data):
        import sys
        sys.exit(1)

    with open(args.data, "r") as f:
        for line in f:
            data.append(json.loads(line))

    categories = set([get_right_cate(item["categories"]) for item in data])
    template = open("paper_template.md", "r").read()
    categories = sorted(categories, key=rank)
    cnt = {cate: 0 for cate in categories}
    for item in data:
        if get_right_cate(item["categories"]) not in cnt.keys():
            continue
        cnt[get_right_cate(item["categories"])] += 1

    markdown = f"<div id=toc></div>\n\n# Table of Contents\n\n"
    for idx, cate in enumerate(categories):
        markdown += f"- [{cate}](#{cate}) [Total: {cnt[cate]}]\n"

    data = sorted(data, key=lambda x: x.get("AI", {}).get("relevance", float('-inf')), reverse=True)

    idx = count(1)
    for cate in categories:
        markdown += f"\n\n<div id='{cate}'></div>\n\n"
        markdown += f"# {cate} [[Back]](#toc)\n\n"
        markdown += "\n\n".join(
            [
                template.format(
                    title=item["title"],
                    authors=",".join(item["authors"]),
                    summary=item["summary"],
                    url=item['abs'],
                    tldr=item['AI']['tldr'],
                    relevance=item['AI']['relevance'],
                    motivation=item['AI']['motivation'],
                    method=item['AI']['method'],
                    result=item['AI']['result'],
                    conclusion=item['AI']['conclusion'],
                    cate=item['categories'][0],
                    idx=next(idx)
                )
                for item in data if get_right_cate(item["categories"]) == cate
            ]
        )
    with open(args.data.split('_')[0] + '.md', "w", encoding="utf-8") as f:
        f.write(markdown)

import json

# 读取 JSON 文件
file_path = "topics.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)  # 解析 JSON 文件



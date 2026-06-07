#!/usr/bin/env python3
"""全文搜索索引构建器 — 从 tagged.md + corpus 生成 search-index.json"""
import json, re
from pathlib import Path

DOCS_DIR = Path("/Users/wukong/Desktop/龙虾场/picc-property-insurance-kb/docs")

# 索引所有 HTML 页面
index = []

# 1. 首页
index.append({
    "title": "PICC企财险知识库 — 首页",
    "category": "导航",
    "url": "index.html",
    "content": "PICC 企财险知识库 32个险种 14,028处实体标注 721个独立实体 22类实体类型"
})

# 2. 概念词条
concepts_dir = DOCS_DIR / "concepts"
for html_file in sorted(concepts_dir.glob("*.html")):
    text = html_file.read_text(encoding='utf-8')
    # 提取标题
    title_match = re.search(r'<title>(.+?) — PICC', text)
    title = title_match.group(1) if title_match else html_file.stem
    
    # 提取正文（去掉HTML标签）
    body = re.sub(r'<style>.*?</style>', '', text, flags=re.DOTALL)
    body = re.sub(r'<script>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    
    if len(body) > 2000:
        body = body[:2000]
    
    index.append({
        "title": title,
        "category": "概念词条",
        "url": f"concepts/{html_file.name}",
        "content": body
    })

# 3. 险种章节
chapters_dir = DOCS_DIR / "chapters"
for html_file in sorted(chapters_dir.glob("*.html")):
    text = html_file.read_text(encoding='utf-8')
    title_match = re.search(r'<title>(.+?) — PICC', text)
    title = title_match.group(1) if title_match else html_file.stem
    
    body = re.sub(r'<style>.*?</style>', '', text, flags=re.DOTALL)
    body = re.sub(r'<script>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    
    if len(body) > 3000:
        body = body[:3000]
    
    index.append({
        "title": f"条款：{title}",
        "category": "险种条款",
        "url": f"chapters/{html_file.name}",
        "content": body
    })

# 4. 实体索引
entities_dir = DOCS_DIR / "entities"
for html_file in sorted(entities_dir.glob("*.html")):
    text = html_file.read_text(encoding='utf-8')
    title_match = re.search(r'<title>(.+?) — PICC', text)
    title = title_match.group(1) if title_match else html_file.stem
    
    body = re.sub(r'<style>.*?</style>', '', text, flags=re.DOTALL)
    body = re.sub(r'<script>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()[:1000]
    
    index.append({
        "title": title,
        "category": "实体索引",
        "url": f"entities/{html_file.name}",
        "content": body
    })

# 保存
output = DOCS_DIR / "search-index.json"
output.write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')

print(f"📊 搜索索引: {len(index)} 个页面")
print(f"   概念词条: {sum(1 for i in index if i['category']=='概念词条')}")
print(f"   险种条款: {sum(1 for i in index if i['category']=='险种条款')}")
print(f"   实体索引: {sum(1 for i in index if i['category']=='实体索引')}")

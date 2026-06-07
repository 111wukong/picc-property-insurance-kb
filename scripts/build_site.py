#!/usr/bin/env python3
"""
批量构建站点：从 corpus/ 生成全部条款的 HTML 阅读页面
- 优先使用 tagged/ 中已有的标注版
- 否则使用 corpus/ 原始文本生成无标注版
"""
import json
import sys
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from render.render_html import render_markdown_to_html

CORPUS_DIR = Path("corpus")
TAGGED_DIR = Path("tagged")
DOCS_CHAPTERS = Path("docs/chapters")

def build_plain_md(meta, txt_path):
    """从纯文本生成简单的 markdown（章节识别 + 条目分段）"""
    text = txt_path.read_text(encoding='utf-8')
    lines = text.strip().split('\n')
    
    md_lines = []
    title_found = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            md_lines.append('')
            continue
        
        # 识别标题行
        if not title_found and len(stripped) < 30:
            # 保险公司名称 → h1
            if '保险' in stripped and ('公司' in stripped or '股份' in stripped):
                md_lines.append(f'# {stripped}')
                title_found = True
                continue
        
        # 识别章节标题（典型格式：2-6个中文字符，不含标点）
        if len(stripped) <= 10 and not any(c in stripped for c in '，。、；：（）()0123456789'):
            if stripped in ['总则', '保险标的', '保险责任', '责任免除', 
                          '保险价值', '保险金额', '免赔额', '免赔率',
                          '保险期间', '保险人义务', '投保人义务', '被保险人义务',
                          '投保人/被保险人义务', '投保人、被保险人义务',
                          '赔偿处理', '争议处理', '其他事项', '附则',
                          '保险价值、保险金额与免赔额（率）',
                          '保险价值、保险金额与免赔额',
                          '释义']:
                md_lines.append(f'## {stripped}')
                continue
        
        # 识别条目编号
        if stripped.startswith('第') and '条' in stripped[:10]:
            md_lines.append(f'**{stripped}**')
        else:
            md_lines.append(stripped)
    
    return '\n\n'.join(md_lines)

def main():
    DOCS_CHAPTERS.mkdir(parents=True, exist_ok=True)
    
    # 加载产品索引
    with open(CORPUS_DIR / 'index.json', 'r') as f:
        index = json.load(f)
    
    built = 0
    tagged = 0
    plain = 0
    
    for product in index['products']:
        pid = product['product_id']
        name = product['product_name']
        safe_name = name.replace('/', '_').replace('\\', '_')
        
        html_path = DOCS_CHAPTERS / f"{pid}_{safe_name}.html"
        
        # 优先检查 tagged 版本
        tagged_paths = list(TAGGED_DIR.glob(f"{pid}_*.md"))
        if tagged_paths:
            tagged_md = tagged_paths[0].read_text(encoding='utf-8')
            html = render_markdown_to_html(tagged_md, title=name)
            tagged += 1
        else:
            # 使用原始文本生成无标注版
            txt_path = CORPUS_DIR / f"{pid}_{safe_name}" / "条款正文.txt"
            if not txt_path.exists():
                # 尝试模糊匹配
                candidates = list(CORPUS_DIR.glob(f"{pid}_*/条款正文.txt"))
                if candidates:
                    txt_path = candidates[0]
                else:
                    print(f"  ⚠️ 找不到正文: {pid}_{safe_name}")
                    continue
            
            md_text = build_plain_md(product, txt_path)
            html = render_markdown_to_html(md_text, title=name)
            plain += 1
        
        html_path.write_text(html, encoding='utf-8')
        built += 1
        print(f"  ✅ [{pid}] {name[:40]}")
    
    print(f"\n📊 构建完成: {built} 页面")
    print(f"   🏷️ 标注版: {tagged}")
    print(f"   📄 纯文本版: {plain}")

if __name__ == '__main__':
    main()

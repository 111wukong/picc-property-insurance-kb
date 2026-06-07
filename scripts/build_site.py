#!/usr/bin/env python3
"""
v2.0 增强构建脚本 — 带章节导航、实体索引
"""
import json
import sys
import urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from render.render_html import render_markdown_to_html, _pn_counter

CORPUS_DIR = Path("corpus")
TAGGED_DIR = Path("tagged")
DOCS_CHAPTERS = Path("docs/chapters")

def build_plain_md(meta, txt_path):
    text = txt_path.read_text(encoding='utf-8')
    lines = text.strip().split('\n')
    md_lines = []
    title_found = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            md_lines.append('')
            continue
        if not title_found and len(stripped) < 30 and '保险' in stripped and ('公司' in stripped or '股份' in stripped):
            md_lines.append(f'# {stripped}')
            title_found = True
            continue
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
        if stripped.startswith('第') and '条' in stripped[:10]:
            md_lines.append(f'**{stripped}**')
        else:
            md_lines.append(stripped)

    return '\n\n'.join(md_lines)

def main():
    DOCS_CHAPTERS.mkdir(parents=True, exist_ok=True)

    with open(CORPUS_DIR / 'index.json', 'r') as f:
        index = json.load(f)

    # 构建产品列表用于导航
    products = []
    for p in index['products']:
        safe_name = p['product_name'].replace('/', '_').replace('\\', '_')
        filename = f"{p['product_id']}_{safe_name}.html"
        products.append({
            'id': p['product_id'],
            'name': p['product_name'][:40],
            'filename': filename,
            'path': f"chapters/{urllib.parse.quote(filename)}",
        })

    built = 0
    tagged_count = 0
    plain_count = 0

    for i, product in enumerate(products):
        pid = product['id']
        safe_name = product['name'].replace('/', '_').replace('\\', '_')
        html_path = DOCS_CHAPTERS / product['filename']

        # 构建导航上下文
        prev_ch = products[i-1] if i > 0 else None
        next_ch = products[i+1] if i < len(products)-1 else None

        # 优先 tagged 版本
        tagged_paths = list(TAGGED_DIR.glob(f"{pid}_*.md"))
        if not tagged_paths:
            tagged_paths = list(TAGGED_DIR.glob(f"*{safe_name[:10]}*.md"))

        if tagged_paths:
            tagged_text = tagged_paths[0].read_text(encoding='utf-8')
            _pn_counter[0] = 0
            html = render_markdown_to_html(
                tagged_text,
                title=product['name'],
                prev_chapter=prev_ch,
                next_chapter=next_ch
            )
            tagged_count += 1
        else:
            txt_path = CORPUS_DIR / f"{pid}_{safe_name}" / "条款正文.txt"
            candidates = list(CORPUS_DIR.glob(f"{pid}_*/条款正文.txt"))
            if not txt_path.exists() and candidates:
                txt_path = candidates[0]
            if txt_path.exists():
                with open(CORPUS_DIR / 'index.json') as f:
                    meta = json.load(f)
                product_meta = next((p for p in meta['products'] if p['product_id'] == pid), None)
                md_text = build_plain_md(product_meta, txt_path)
                _pn_counter[0] = 0
                html = render_markdown_to_html(
                    md_text,
                    title=product['name'],
                    prev_chapter=prev_ch,
                    next_chapter=next_ch
                )
                plain_count += 1
            else:
                print(f"  ⚠️ 找不到: {pid}")
                continue

        html_path.write_text(html, encoding='utf-8')
        built += 1
        nav = f"[{i+1}/{len(products)}]"
        print(f"  ✅ {nav} [{pid}] {product['name'][:40]}")

    print(f"\n📊 构建完成: {built} 页面")
    print(f"   🏷️ 标注版: {tagged_count}")
    print(f"   📄 纯文本版: {plain_count}")

if __name__ == '__main__':
    main()

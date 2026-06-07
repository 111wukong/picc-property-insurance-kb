#!/usr/bin/env python3
"""
PICC企财险知识库 — tagged.md → HTML 渲染器
借鉴 shiji-kb 的 render_shiji_html.py 标注语法，适配保险领域实体类型

标注语法：
  名词实体（23类）：〖MARKER 显示文本〗 或 〖MARKER 显示文本|规范名〗
  关系标注（内联）：不渲染为可见元素，用于KG构建

实体标记映射（详见 ontology/entity-types.json）：
  @ 险种名    § 章节    ¶ 条目    № 备案号    + 附加险    ≡ 特别约定    ↗ 版本引用
  ☐ 保险标的  ⚡ 保险责任  ✕ 责任免除  $ 保险金额  % 免赔额  ⏱ 保险期间  ¥ 费率
  ⛓ 赔偿处理  ◈ 义务条款  ⚖ 定义条款
  ▶ 投保人    ◀ 保险人    ◆ 被保险人  📋 合同单据  ▣ 第三方
"""
import re
import json
import sys
from pathlib import Path
from html import escape as html_escape
import urllib.parse

# ====================== 实体标注映射 ======================
ENTITY_MAP = {
    # 一级：条款结构（8类）
    '@':  ('entity-product',      '险种名',     '#D4380D'),
    '§':  ('entity-section',      '条款章节',   '#1D39C4'),
    '¶':  ('entity-article',      '具体条目',   '#531DAB'),
    '№':  ('entity-filing',       '备案号',     '#595959'),
    '+':  ('entity-rider',        '附加险',     '#FA8C16'),
    '≡':  ('entity-special',      '特别约定',   '#EB2F96'),
    '↗':  ('entity-version',      '版本引用',   '#08979C'),

    # 二级：保险核心概念（10类）
    '☐':  ('entity-subject',      '保险标的',   '#237804'),
    '⚡':  ('entity-peril',        '保险责任',   '#FAAD14'),
    '✕':  ('entity-exclusion',    '责任免除',   '#FF4D4F'),
    '$':  ('entity-sum',          '保险金额',   '#13C2C2'),
    '%':  ('entity-deductible',   '免赔额/率',  '#F759AB'),
    '⏱':  ('entity-period',       '保险期间',   '#2F54EB'),
    '¥':  ('entity-rate',         '费率',       '#722ED1'),
    '⛓':  ('entity-claim',        '赔偿处理',   '#FA541C'),
    '◈':  ('entity-obligation',   '义务条款',   '#A0D911'),
    '⚖':  ('entity-definition',   '定义条款',   '#597EF7'),

    # 三级：合同主体与单据（5类）
    '▶':  ('entity-policyholder', '投保人',     '#5B8C00'),
    '◀':  ('entity-insurer',      '保险人',     '#096DD9'),
    '◆':  ('entity-insured',      '被保险人',   '#7CB305'),
    '📋':  ('entity-document',     '合同单据',   '#AD8B00'),
    '▣':  ('entity-thirdparty',   '第三方',     '#C41D7F'),
}

# 构建正则表达式
def build_patterns():
    patterns = []
    for marker, (css_class, entity_name, color) in ENTITY_MAP.items():
        escaped_marker = re.escape(marker)
        # 消歧格式: 〖MARKER 显示名|规范名〗
        disambig = re.compile(
            rf'〖{escaped_marker}\s+([^〖〗|]+)\|([^〖〗]+)〗'
        )
        # 普通格式: 〖MARKER 显示文本〗
        normal = re.compile(
            rf'〖{escaped_marker}\s+([^〖〗]+)〗'
        )
        patterns.append((disambig, normal, css_class, entity_name, color, marker))
    return patterns

PATTERNS = build_patterns()

# ====================== 渲染函数 ======================
def render_entity(match, css_class, entity_name, color, marker, canonical=None):
    """渲染实体为带 tooltip 的 span"""
    display_text = match.group(1).strip()
    if canonical:
        canonical_text = match.group(2).strip()
    else:
        canonical_text = display_text

    title = f"{entity_name}"
    if canonical_text != display_text:
        title += f" | 规范名：{canonical_text}"

    # 生成实体链接（跳转到词条页）
    entity_slug = urllib.parse.quote(canonical_text)
    link = f'/entities/{entity_slug}.html'

    return (
        f'<a href="{link}" class="{css_class}" '
        f'title="{html_escape(title)}" '
        f'data-entity="{html_escape(canonical_text)}" '
        f'data-type="{html_escape(entity_name)}" '
        f'style="--entity-color:{color}">'
        f'{html_escape(display_text)}'
        f'</a>'
    )

def render_paragraph(text):
    """渲染一个段落内的实体标注"""
    result = text

    for disambig_pat, normal_pat, css_class, entity_name, color, marker in PATTERNS:
        # 先处理消歧格式
        def make_disambig_replacer(cls, name, col):
            return lambda m: render_entity(m, cls, name, col, marker, canonical=True)
        result = re.sub(disambig_pat, make_disambig_replacer(css_class, entity_name, color), result)

        # 再处理普通格式
        def make_normal_replacer(cls, name, col):
            return lambda m: render_entity(m, cls, name, col, marker)
        result = re.sub(normal_pat, make_normal_replacer(css_class, entity_name, color), result)

    return result

def render_markdown_to_html(md_text, title=None):
    """将 tagged.md 渲染为完整 HTML 页面"""
    lines = md_text.strip().split('\n')

    # 提取标题（如果首行是 # 标题）
    if title is None:
        title = ""
    body_lines = []
    in_meta = True

    for line in lines:
        stripped = line.strip()
        if not stripped:
            body_lines.append('<br>')
            continue

        # Markdown 标题
        if stripped.startswith('# '):
            h1_text = stripped[2:].strip()
            if not title:
                title = h1_text
            body_lines.append(f'<h1>{html_escape(h1_text)}</h1>')
        elif stripped.startswith('## '):
            h2_text = stripped[3:].strip()
            body_lines.append(f'<h2>{html_escape(h2_text)}</h2>')
        elif stripped.startswith('### '):
            h3_text = stripped[4:].strip()
            body_lines.append(f'<h3>{html_escape(h3_text)}</h3>')
        elif stripped.startswith('- ') or stripped.startswith('* '):
            item_text = stripped[2:].strip()
            rendered = render_paragraph(item_text)
            body_lines.append(f'<li>{rendered}</li>')
        elif re.match(r'^\d+[\.\、]', stripped):
            item_text = re.sub(r'^\d+[\.\、]\s*', '', stripped)
            rendered = render_paragraph(item_text)
            body_lines.append(f'<li>{rendered}</li>')
        else:
            rendered = render_paragraph(stripped)
            body_lines.append(f'<p>{rendered}</p>')

    body_html = '\n'.join(body_lines)

    # CSS
    entity_styles = []
    for marker, (css_class, name, color) in ENTITY_MAP.items():
        entity_styles.append(f'''
      .{css_class} {{
        color: {color};
        text-decoration: underline;
        text-decoration-color: {color}33;
        text-underline-offset: 3px;
        cursor: pointer;
        transition: all 0.2s;
        padding: 0 2px;
        border-radius: 2px;
      }}
      .{css_class}:hover {{
        background: {color}18;
        text-decoration-color: {color};
      }}''')

    entity_css = '\n'.join(entity_styles)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_escape(title)} — PICC企财险知识库</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg: #FAFBFC;
    --text: #1A1A2E;
    --text2: #5A6178;
    --border: #E8ECF1;
    --card: #FFFFFF;
    --accent: #D4380D;
    --serif: 'Noto Serif SC', 'Source Han Serif SC', 'STSong', 'SimSun', 'Songti SC', Georgia, 'Times New Roman', serif;
    --sans: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif;
  }}

  body {{
    font-family: var(--serif);
    color: var(--text);
    background: var(--bg);
    line-height: 2.0;
    font-size: 17px;
    -webkit-font-smoothing: antialiased;
  }}

  .container {{
    max-width: 780px;
    margin: 0 auto;
    padding: 60px 24px 120px;
  }}

  h1 {{
    font-size: 28px;
    font-weight: 900;
    color: var(--accent);
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 3px solid var(--accent);
    letter-spacing: 1px;
  }}

  h2 {{
    font-size: 22px;
    font-weight: 700;
    color: #1D39C4;
    margin: 40px 0 16px;
    padding-left: 12px;
    border-left: 4px solid #1D39C4;
  }}

  h3 {{
    font-size: 18px;
    font-weight: 600;
    color: #531DAB;
    margin: 24px 0 12px;
  }}

  p {{
    margin: 8px 0;
    text-indent: 2em;
    text-align: justify;
  }}

  li {{
    margin: 4px 0 4px 2em;
  }}

  br + p {{ text-indent: 2em; }}
  br + br {{ display: none; }}

  /* 实体标注样式 */
{entity_css}

  /* 响应式 */
  @media (max-width: 768px) {{
    .container {{
      padding: 32px 16px 80px;
    }}
    h1 {{ font-size: 22px; }}
    h2 {{ font-size: 18px; }}
    body {{ font-size: 15px; }}
  }}

  /* 打印 */
  @media print {{
    body {{ background: white; }}
    .container {{ max-width: 100%; padding: 0; }}
  }}
</style>
</head>
<body>
<div class="container">
{body_html}
</div>
</body>
</html>'''

    return html

def render_file(input_path, output_path, title=None):
    """渲染单个 tagged.md 文件"""
    md_text = Path(input_path).read_text(encoding='utf-8')
    html = render_markdown_to_html(md_text, title=title)
    Path(output_path).write_text(html, encoding='utf-8')
    print(f"  ✅ {input_path} → {output_path}")

def main():
    if len(sys.argv) < 2:
        print("用法: python render_html.py <input.tagged.md> [output.html]")
        print("      python render_html.py --batch <tagged_dir> <output_dir>")
        sys.exit(1)

    if sys.argv[1] == '--batch':
        tagged_dir = Path(sys.argv[2])
        output_dir = Path(sys.argv[3])
        output_dir.mkdir(parents=True, exist_ok=True)
        for md_file in sorted(tagged_dir.glob('*.md')):
            out_file = output_dir / f"{md_file.stem}.html"
            render_file(md_file, out_file)
    else:
        input_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix('.html')
        render_file(input_path, output_path)

if __name__ == '__main__':
    main()

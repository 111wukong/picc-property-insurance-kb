#!/usr/bin/env python3
"""
PICC企财险知识库 — tagged.md → HTML 渲染器 v2.0
借鉴 shiji-kb 的阅读器架构，新增：
  - Purple Numbers 段落编号（可点击复制链接）
  - 章节前后导航（上一页/下一页/回首页）
  - 实体链接 → 实体索引页
  - 语法高亮开关（齿轮按钮，持久化 localStorage）
  - 滚动进度条
  - 响应式侧边栏导航
"""
import re
import json
import sys
from pathlib import Path
from html import escape as html_escape
import urllib.parse

ENTITY_MAP = {
    '@':  ('entity-product',      '险种名',     '#D4380D'),
    '§':  ('entity-section',      '条款章节',   '#1D39C4'),
    '¶':  ('entity-article',      '具体条目',   '#531DAB'),
    '№':  ('entity-filing',       '备案号',     '#595959'),
    '+':  ('entity-rider',        '附加险',     '#FA8C16'),
    '≡':  ('entity-special',      '特别约定',   '#EB2F96'),
    '↗':  ('entity-version',      '版本引用',   '#08979C'),
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
    '▶':  ('entity-policyholder', '投保人',     '#5B8C00'),
    '◀':  ('entity-insurer',      '保险人',     '#096DD9'),
    '◆':  ('entity-insured',      '被保险人',   '#7CB305'),
    '📋':  ('entity-document',     '合同单据',   '#AD8B00'),
    '▣':  ('entity-thirdparty',   '第三方',     '#C41D7F'),
}

def build_patterns():
    patterns = []
    for marker, (css_class, entity_name, color) in ENTITY_MAP.items():
        escaped_marker = re.escape(marker)
        disambig = re.compile(rf'〖{escaped_marker}\s*([^〖〗|]+)\|([^〖〗]+)〗')
        normal = re.compile(rf'〖{escaped_marker}\s*([^〖〗]+)〗')
        patterns.append((disambig, normal, css_class, entity_name, color, marker))
    return patterns

PATTERNS = build_patterns()

# ====================== 全局状态 ======================
_pn_counter = [0]  # 段落编号计数器

def render_entity(match, css_class, entity_name, color, marker, canonical=None):
    display_text = match.group(1).strip()
    if canonical:
        canonical_text = match.group(2).strip()
    else:
        canonical_text = display_text

    title = entity_name
    if canonical_text != display_text:
        title += f" | 规范名：{canonical_text}"

    # 链接到实体索引页 (按类型分组)
    type_slug = css_class.replace('entity-', '')
    entity_slug = urllib.parse.quote(canonical_text)
    link = f'../entities/{type_slug}.html#entity-{entity_slug}'

    return (
        f'<a href="{link}" class="{css_class} entity-tagged" '
        f'title="{html_escape(title)}" '
        f'data-entity="{html_escape(canonical_text)}" '
        f'data-type="{html_escape(entity_name)}">'
        f'{html_escape(display_text)}'
        f'</a>'
    )

def render_paragraph(text):
    result = text
    for disambig_pat, normal_pat, css_class, entity_name, color, marker in PATTERNS:
        result = re.sub(disambig_pat,
            lambda m, c=css_class, n=entity_name, cl=color: render_entity(m, c, n, cl, marker, True),
            result)
        result = re.sub(normal_pat,
            lambda m, c=css_class, n=entity_name, cl=color: render_entity(m, c, n, cl, marker),
            result)
    return result

def next_pn():
    _pn_counter[0] += 1
    return str(_pn_counter[0])

def render_markdown_to_html(md_text, title=None, chapter_index=None, prev_chapter=None, next_chapter=None):
    lines = md_text.strip().split('\n')
    if title is None:
        title = ""
    body_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            body_lines.append('<br>')
            continue

        if stripped.startswith('# '):
            h1_text = stripped[2:].strip()
            # 移除实体标注用于纯标题
            clean_title = re.sub(r'[〖〗].*?[〖〗]', '', h1_text)
            clean_title = re.sub(r'〖[^〗]+〗', '', clean_title)
            if not title:
                title = clean_title
            body_lines.append(f'<h1>{html_escape(h1_text)}</h1>')
        elif stripped.startswith('## '):
            h2_text = stripped[3:].strip()
            body_lines.append(f'<h2 id="section-{next_pn()}">{html_escape(h2_text)}</h2>')
        elif stripped.startswith('### '):
            h3_text = stripped[4:].strip()
            body_lines.append(f'<h3>{html_escape(h3_text)}</h3>')
        elif stripped.startswith('<table') or stripped.startswith('<thead') or stripped.startswith('<tbody') or stripped.startswith('<tr') or stripped.startswith('<td') or stripped.startswith('<th') or stripped.startswith('</table') or stripped.startswith('</tr') or stripped.startswith('</td') or stripped.startswith('</th') or stripped.startswith('</thead') or stripped.startswith('</tbody'):
            # HTML表格直通
            body_lines.append(stripped)
            item_text = stripped[2:].strip()
            rendered = render_paragraph(item_text)
            body_lines.append(f'<li>{rendered}</li>')
        elif re.match(r'^\d+[\.\、]', stripped):
            item_text = re.sub(r'^\d+[\.\、]\s*', '', stripped)
            rendered = render_paragraph(item_text)
            body_lines.append(f'<li>{rendered}</li>')
        else:
            pn = next_pn()
            rendered = render_paragraph(stripped)
            body_lines.append(
                f'<p id="pn-{pn}">'
                f'<a href="#pn-{pn}" class="pn-link" title="复制此段落链接">[{pn}]</a> '
                f'{rendered}'
                f'</p>'
            )

    body_html = '\n'.join(body_lines)

    # 段落编号计数
    total_paragraphs = _pn_counter[0]

    # 实体 CSS
    entity_styles = []
    for marker, (css_class, name, color) in ENTITY_MAP.items():
        entity_styles.append(f'''
      .{css_class} {{
        color: {color};
        text-decoration: underline;
        text-decoration-color: {color}40;
        text-underline-offset: 3px;
        cursor: pointer;
        transition: all 0.2s;
        padding: 0 1px;
        border-radius: 2px;
      }}
      .{css_class}:hover {{
        background: {color}18;
        text-decoration-color: {color};
      }}''')

    entity_css = '\n'.join(entity_styles)

    # 导航 HTML
    nav_html = ''
    if prev_chapter or next_chapter:
        nav_html = '<nav class="chapter-nav">'
        if prev_chapter:
            nav_html += f'<a href="{prev_chapter["path"]}" class="nav-prev">← {prev_chapter["name"]}</a>'
        else:
            nav_html += '<span class="nav-prev nav-disabled">← 已是第一篇</span>'
        nav_html += '<a href="../index.html" class="nav-home">🏠 目录</a>'
        if next_chapter:
            nav_html += f'<a href="{next_chapter["path"]}" class="nav-next">{next_chapter["name"]} →</a>'
        else:
            nav_html += '<span class="nav-next nav-disabled">已是最后一篇 →</span>'
        nav_html += '</nav>'

    # 侧边栏目录生成
    toc_items = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## '):
            h2_text = stripped[3:].strip()
            clean = re.sub(r'〖[^〗]+〗', '', h2_text)
            toc_items.append(f'<a href="#section-{toc_items.__len__() + 1 if hasattr(toc_items, "__len__") else 1}" class="toc-link">{html_escape(clean)}</a>')

    # Fix: regenerate toc with proper section IDs
    toc_items = []
    section_id = 1
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('## '):
            h2_text = stripped[3:].strip()
            clean = re.sub(r'〖[^〗]+〗', '', h2_text)
            toc_items.append(f'<a href="#section-{section_id}" class="toc-link">{html_escape(clean)}</a>')
            section_id += 1

    toc_html = '\n          '.join(toc_items) if toc_items else '<span class="toc-empty">无章节</span>'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_escape(title)} — PICC企财险知识库</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700;900&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg: #FAFBFC;
    --text: #1A1A2E;
    --text2: #5A6178;
    --border: #E8ECF1;
    --card: #FFFFFF;
    --accent: #D4380D;
    --blue: #1D39C4;
    --serif: 'Noto Serif SC', 'Source Han Serif SC', 'STSong', 'SimSun', 'Songti SC', Georgia, 'Times New Roman', serif;
    --sans: 'DM Sans', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif;
    --sidebar-w: 240px;
  }}

  body {{
    font-family: var(--serif);
    color: var(--text);
    background: var(--bg);
    line-height: 2.0;
    font-size: 17px;
    -webkit-font-smoothing: antialiased;
  }}

  /* ===== 顶部导航 ===== */
  .chapter-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 780px;
    margin: 0 auto;
    padding: 12px 24px;
    font-size: 13px;
    font-family: var(--sans);
    gap: 12px;
    flex-wrap: wrap;
  }}
  .chapter-nav a {{
    color: var(--blue);
    text-decoration: none;
    padding: 4px 12px;
    border-radius: 4px;
    transition: background 0.2s;
    white-space: nowrap;
  }}
  .chapter-nav a:hover {{ background: var(--border); }}
  .nav-disabled {{ color: #C0C4CC; padding: 4px 12px; white-space: nowrap; }}
  .nav-home {{ font-weight: 600; }}

  /* ===== 滚动进度条 ===== */
  .progress-bar {{
    position: fixed;
    top: 0; left: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--blue));
    z-index: 1000;
    transition: width 0.1s linear;
  }}

  /* ===== 主内容区 ===== */
  .main-wrapper {{
    display: flex;
    max-width: 1100px;
    margin: 0 auto;
    padding: 20px 24px 80px;
    gap: 32px;
  }}

  .container {{
    flex: 1;
    min-width: 0;
    max-width: 780px;
  }}

  /* ===== 侧边栏 ===== */
  .sidebar {{
    width: var(--sidebar-w);
    flex-shrink: 0;
    position: sticky;
    top: 20px;
    align-self: flex-start;
    max-height: calc(100vh - 40px);
    overflow-y: auto;
  }}
  .sidebar::-webkit-scrollbar {{ width: 3px; }}
  .sidebar::-webkit-scrollbar-thumb {{ background: #D1D9E6; border-radius: 2px; }}

  .sidebar-box {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
  }}
  .sidebar-box h4 {{
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 600;
    color: var(--text2);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }}
  .toc-link {{
    display: block;
    font-size: 13px;
    color: var(--text2);
    text-decoration: none;
    padding: 3px 0;
    transition: color 0.15s;
    font-family: var(--sans);
  }}
  .toc-link:hover {{ color: var(--accent); }}
  .toc-empty {{ color: #C0C4CC; font-size: 12px; }}

  /* 高亮开关按钮 */
  .toggle-btn {{
    display: block;
    width: 100%;
    padding: 8px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    color: var(--text2);
    font-family: var(--sans);
    transition: all 0.2s;
  }}
  .toggle-btn:hover {{ border-color: var(--accent); color: var(--accent); }}

  .sidebar-stats {{
    font-size: 11px;
    color: var(--text2);
    font-family: var(--sans);
    line-height: 1.6;
  }}

  /* ===== 标题 ===== */
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
    color: var(--blue);
    margin: 40px 0 16px;
    padding-left: 12px;
    border-left: 4px solid var(--blue);
    scroll-margin-top: 20px;
  }}
  h3 {{
    font-size: 18px;
    font-weight: 600;
    color: #531DAB;
    margin: 24px 0 12px;
  }}

  /* ===== 段落 ===== */
  p {{
    margin: 6px 0;
    text-align: justify;
    position: relative;
    scroll-margin-top: 16px;
  }}

  /* ===== Purple Numbers ===== */
  .pn-link {{
    display: inline-block;
    font-family: var(--sans);
    font-size: 11px;
    color: #ADB5BD;
    text-decoration: none;
    margin-right: 6px;
    user-select: none;
    transition: color 0.15s;
  }}
  .pn-link:hover {{ color: var(--accent); }}
  p:target {{ background: #FFF7E6; border-radius: 4px; padding: 2px 6px; margin: 4px -6px; }}

  li {{ margin: 4px 0 4px 2em; }}

  /* ===== 实体标注 ===== */
{entity_css}

  /* 高亮关闭状态 */
  body.highlight-off .entity-tagged {{
    color: inherit !important;
    text-decoration: none !important;
    background: none !important;
    cursor: default;
  }}

  /* ===== 页脚 ===== */
  .page-footer {{
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    color: var(--text2);
    font-family: var(--sans);
  }}
  .page-footer a {{ color: var(--blue); }}

  /* ===== 表格 ===== */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 14px;
  }}
  table th {{
    background: #1D39C4;
    color: white;
    padding: 8px 14px;
    text-align: center;
    font-weight: 600;
    font-family: var(--sans);
  }}
  table td {{
    padding: 8px 14px;
    text-align: center;
    border: 1px solid var(--border);
    font-family: var(--sans);
  }}
  table tr:nth-child(even) {{ background: #F8F9FC; }}
  table tr:hover {{ background: #EBF0FA; }}
  .rate-table {{ max-width: 400px; }}

  /* ===== 响应式 ===== */
  @media (max-width: 900px) {{
    .main-wrapper {{
      flex-direction: column;
      padding: 12px 16px 60px;
    }}
    .sidebar {{
      width: 100%;
      position: static;
      max-height: none;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .sidebar-box {{ flex: 1; min-width: 140px; }}
    h1 {{ font-size: 22px; }}
    h2 {{ font-size: 18px; }}
    body {{ font-size: 15px; }}
    .chapter-nav {{ padding: 8px 12px; font-size: 12px; }}
  }}

  @media print {{
    .sidebar, .progress-bar, .chapter-nav, .page-footer {{ display: none; }}
    body {{ background: white; }}
    .container {{ max-width: 100%; padding: 0; }}
    .main-wrapper {{ padding: 0; }}
  }}
</style>
</head>
<body>
<div class="progress-bar" id="progress-bar"></div>

{nav_html}

<div class="main-wrapper">
  <aside class="sidebar">
    <div class="sidebar-box">
      <h4>📑 本章目录</h4>
      {toc_html}
    </div>
    <div class="sidebar-box">
      <h4>⚙️ 设置</h4>
      <button class="toggle-btn" id="toggle-highlight" onclick="toggleHighlight()">
        🎨 语法高亮：开
      </button>
    </div>
    <div class="sidebar-box">
      <h4>📊 统计</h4>
      <div class="sidebar-stats">
        段落编号: {total_paragraphs}<br>
        <a href="../index.html">← 返回知识库首页</a>
      </div>
    </div>
  </aside>

  <main class="container">
{body_html}
  </main>
</div>

{nav_html.replace('chapter-nav"', 'chapter-nav chapter-nav-bottom"')}

<div class="page-footer" style="max-width:780px;margin:0 auto;padding:24px;">
  <p>PICC企财险知识库 · <a href="../index.html">返回首页</a> · 许可证: CC BY-NC-SA 4.0</p>
  <p style="margin-top:4px;">条款原文版权归属中国人民财产保险股份有限公司，本项目仅做学术和技术研究用途。</p>
</div>

<script>
// 滚动进度条
window.addEventListener('scroll', () => {{
  const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
  const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
  const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
  document.getElementById('progress-bar').style.width = progress + '%';
}});

// 语法高亮开关
function toggleHighlight() {{
  const body = document.body;
  const btn = document.getElementById('toggle-highlight');
  body.classList.toggle('highlight-off');
  if (body.classList.contains('highlight-off')) {{
    btn.innerHTML = '🎨 语法高亮：关';
    localStorage.setItem('picc-kb-highlight', 'off');
  }} else {{
    btn.innerHTML = '🎨 语法高亮：开';
    localStorage.setItem('picc-kb-highlight', 'on');
  }}
}}

// 恢复用户偏好
if (localStorage.getItem('picc-kb-highlight') === 'off') {{
  document.body.classList.add('highlight-off');
  document.getElementById('toggle-highlight').innerHTML = '🎨 语法高亮：关';
}}

// 点击段落编号复制链接
document.querySelectorAll('.pn-link').forEach(link => {{
  link.addEventListener('click', function(e) {{
    e.preventDefault();
    const url = window.location.origin + window.location.pathname + this.getAttribute('href');
    navigator.clipboard.writeText(url).then(() => {{
      const orig = this.textContent;
      this.textContent = '✓已复制';
      this.style.color = '#237804';
      setTimeout(() => {{ this.textContent = orig; this.style.color = ''; }}, 1500);
    }});
  }});
}});
</script>
</body>
</html>'''

    return html

def render_file(input_path, output_path, title=None, product_index=None):
    md_text = Path(input_path).read_text(encoding='utf-8')
    global _pn_counter
    _pn_counter = [0]
    html = render_markdown_to_html(md_text, title=title, chapter_index=product_index)
    Path(output_path).write_text(html, encoding='utf-8')
    return len(html)

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
            size = render_file(md_file, out_file)
            print(f"  ✅ {md_file.name} → {size:,} bytes")
    else:
        input_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix('.html')
        size = render_file(input_path, output_path)
        print(f"  ✅ {input_path} → {output_path} ({size:,} bytes)")

if __name__ == '__main__':
    main()

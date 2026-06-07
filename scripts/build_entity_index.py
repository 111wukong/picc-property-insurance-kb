#!/usr/bin/env python3
"""
实体索引构建器 — 扫描全部 tagged.md，生成按类型分组的实体索引页
输出到 docs/entities/ 目录
"""
import re
import json
import urllib.parse
from pathlib import Path
from collections import defaultdict
from html import escape as html_escape

TAGGED_DIR = Path("/Users/wukong/Desktop/龙虾场/picc-property-insurance-kb/tagged")
DOCS_DIR = Path("/Users/wukong/Desktop/龙虾场/picc-property-insurance-kb/docs")
ENTITIES_DIR = DOCS_DIR / "entities"

ENTITY_MAP = {
    '@':  ('product',       '险种名',     '#D4380D'),
    '§':  ('section',       '条款章节',   '#1D39C4'),
    '¶':  ('article',       '具体条目',   '#531DAB'),
    '№':  ('filing',        '备案号',     '#595959'),
    '+':  ('rider',         '附加险',     '#FA8C16'),
    '≡':  ('special',       '特别约定',   '#EB2F96'),
    '↗':  ('version',       '版本引用',   '#08979C'),
    '☐':  ('subject',       '保险标的',   '#237804'),
    '⚡':  ('peril',         '保险责任',   '#FAAD14'),
    '✕':  ('exclusion',     '责任免除',   '#FF4D4F'),
    '$':  ('sum',           '保险金额',   '#13C2C2'),
    '%':  ('deductible',    '免赔额/率',  '#F759AB'),
    '⏱':  ('period',        '保险期间',   '#2F54EB'),
    '¥':  ('rate',          '费率',       '#722ED1'),
    '⛓':  ('claim',         '赔偿处理',   '#FA541C'),
    '◈':  ('obligation',    '义务条款',   '#A0D911'),
    '⚖':  ('definition',    '定义条款',   '#597EF7'),
    '▶':  ('policyholder',  '投保人',     '#5B8C00'),
    '◀':  ('insurer',       '保险人',     '#096DD9'),
    '◆':  ('insured',       '被保险人',   '#7CB305'),
    '📋':  ('document',      '合同单据',   '#AD8B00'),
    '▣':  ('thirdparty',    '第三方',     '#C41D7F'),
}

def extract_entities():
    """扫描所有 tagged.md，提取实体"""
    # 按实体类型分组: {type_slug: {entity_name: [occurrences]}}
    entities = defaultdict(lambda: defaultdict(list))

    for md_file in sorted(TAGGED_DIR.glob("*.md")):
        text = md_file.read_text(encoding='utf-8')
        chapter_name = md_file.stem

        for marker, (type_slug, type_name, color) in ENTITY_MAP.items():
            escaped = re.escape(marker)
            # 匹配普通格式和消歧格式
            pattern = rf'〖{escaped}\s*([^〖〗]+)〗'
            for match in re.finditer(pattern, text):
                entity_text = match.group(1).strip()
                # 消歧格式: 显示名|规范名
                if '|' in entity_text:
                    display, canonical = entity_text.split('|', 1)
                    canonical = canonical.strip()
                else:
                    canonical = entity_text

                entities[type_slug][canonical].append({
                    'display': entity_text.split('|')[0].strip() if '|' in entity_text else entity_text,
                    'chapter': chapter_name,
                })

    return entities

def build_entity_page(type_slug, type_name, color, entity_dict):
    """为一种实体类型生成索引页"""
    sorted_entities = sorted(entity_dict.items(), key=lambda x: len(x[1]), reverse=True)

    items_html = []
    for entity_name, occurrences in sorted_entities:
        entity_id = f"entity-{urllib.parse.quote(entity_name)}"
        # 去重章节
        chapters = list(dict.fromkeys(o['chapter'] for o in occurrences))
        chapter_links = ', '.join(
            f'<a href="../chapters/{urllib.parse.quote(c)}.html">{html_escape(c[:30])}</a>'
            for c in chapters[:5]
        )
        if len(chapters) > 5:
            chapter_links += f' ... 等{len(chapters)}个险种'

        items_html.append(f'''
        <tr id="{entity_id}">
          <td class="entity-name" style="color:{color}">{html_escape(entity_name)}</td>
          <td class="entity-count">{len(occurrences)}</td>
          <td class="entity-chapters">{chapter_links}</td>
        </tr>''')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{type_name} — 实体索引 — PICC企财险知识库</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: #FAFBFC;
    color: #1A1A2E;
    line-height: 1.6;
    padding: 40px 24px;
  }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{
    font-size: 24px;
    font-weight: 700;
    color: {color};
    margin-bottom: 8px;
  }}
  .subtitle {{ color: #5A6178; font-size: 14px; margin-bottom: 24px; }}
  .back-link {{ display: inline-block; margin-bottom: 20px; color: #1D39C4; font-size: 13px; text-decoration: none; }}
  .back-link:hover {{ text-decoration: underline; }}

  .search-box {{
    width: 100%;
    padding: 10px 16px;
    border: 1px solid #E8ECF1;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 20px;
    outline: none;
    transition: border-color 0.2s;
  }}
  .search-box:focus {{ border-color: {color}; }}

  table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  }}
  th {{
    background: #F0F2F5;
    padding: 10px 16px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    color: #5A6178;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  td {{
    padding: 10px 16px;
    border-top: 1px solid #F0F2F5;
    font-size: 13px;
  }}
  .entity-name {{ font-weight: 600; }}
  .entity-count {{ color: #5A6178; text-align: center; white-space: nowrap; }}
  .entity-chapters {{ font-size: 12px; color: #8C8C8C; }}
  .entity-chapters a {{ color: #1D39C4; text-decoration: none; }}
  .entity-chapters a:hover {{ text-decoration: underline; }}
  tr:hover {{ background: #FAFBFC; }}

  .stats {{ font-size: 12px; color: #8C8C8C; margin-bottom: 16px; }}

  @media (max-width: 768px) {{
    body {{ padding: 20px 12px; }}
    td {{ padding: 8px 10px; font-size: 12px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <a href="../index.html" class="back-link">← 返回知识库首页</a>
  <h1>{type_name} <span style="font-size:16px;font-weight:400">({marker_from_type(type_slug)})</span></h1>
  <p class="subtitle">共 {len(sorted_entities)} 个实体，{sum(len(v) for v in entity_dict.values())} 次出现</p>

  <input type="text" class="search-box" placeholder="🔍 搜索实体..." oninput="filterEntities(this.value)">

  <table id="entity-table">
    <thead>
      <tr>
        <th>实体名称</th>
        <th style="text-align:center">出现次数</th>
        <th>出现险种</th>
      </tr>
    </thead>
    <tbody>
      {''.join(items_html)}
    </tbody>
  </table>
</div>

<script>
function filterEntities(query) {{
  const rows = document.querySelectorAll('#entity-table tbody tr');
  const q = query.toLowerCase();
  rows.forEach(row => {{
    const name = row.querySelector('.entity-name').textContent.toLowerCase();
    row.style.display = name.includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>'''

    return html

def marker_from_type(type_slug):
    """从type_slug反查marker"""
    for marker, (slug, _, _) in ENTITY_MAP.items():
        if slug == type_slug:
            return marker
    return ''

def build_overview_page(type_stats):
    """生成实体索引总览页"""
    items = []
    for type_slug, (type_name, color, count) in sorted(type_stats.items(), key=lambda x: x[1][2], reverse=True):
        marker = marker_from_type(type_slug)
        items.append(f'''
        <a href="{type_slug}.html" class="type-card">
          <div class="type-marker" style="background:{color}">{marker}</div>
          <div class="type-info">
            <div class="type-name">{type_name}</div>
            <div class="type-count">{count} 个实体</div>
          </div>
        </a>''')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>实体索引 — PICC企财险知识库</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: #FAFBFC;
    color: #1A1A2E;
    padding: 40px 24px;
  }}
  .container {{ max-width: 700px; margin: 0 auto; }}
  h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 8px; }}
  .subtitle {{ color: #5A6178; font-size: 14px; margin-bottom: 24px; }}
  .back-link {{ display: inline-block; margin-bottom: 20px; color: #1D39C4; font-size: 13px; text-decoration: none; }}

  .type-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px;
  }}
  .type-card {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    background: white;
    border: 1px solid #E8ECF1;
    border-radius: 8px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
  }}
  .type-card:hover {{
    border-color: #D4380D;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transform: translateY(-1px);
  }}
  .type-marker {{
    width: 36px; height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 16px;
    font-weight: 700;
    flex-shrink: 0;
  }}
  .type-name {{ font-size: 14px; font-weight: 600; }}
  .type-count {{ font-size: 12px; color: #8C8C8C; margin-top: 2px; }}
</style>
</head>
<body>
<div class="container">
  <a href="../index.html" class="back-link">← 返回知识库首页</a>
  <h1>📇 实体索引</h1>
  <p class="subtitle">全部 22 类实体 · 按类型浏览</p>

  <div class="type-grid">
    {''.join(items)}
  </div>
</div>
</body>
</html>'''
    return html

def main():
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    print("🔍 扫描 tagged.md 提取实体...")

    entities = extract_entities()
    type_stats = {}

    valid_slugs = {v[0] for v in ENTITY_MAP.values()}
    for type_slug, entity_dict in entities.items():
        if type_slug not in valid_slugs:
            continue
        # 找到对应的 type_name 和 color
        type_name = None
        color = None
        for marker, (slug, name, col) in ENTITY_MAP.items():
            if slug == type_slug:
                type_name = name
                color = col
                break

        if not type_name:
            continue

        count = len(entity_dict)
        type_stats[type_slug] = (type_name, color, count)

        html = build_entity_page(type_slug, type_name, color, entity_dict)
        output_path = ENTITIES_DIR / f"{type_slug}.html"
        output_path.write_text(html, encoding='utf-8')
        print(f"  ✅ {type_name} ({type_slug}): {count} 个实体 → {output_path.name}")

    # 生成总览页
    overview = build_overview_page(type_stats)
    (ENTITIES_DIR / "index.html").write_text(overview, encoding='utf-8')
    print(f"\n📊 总览页: entities/index.html")
    print(f"   共 {sum(s[2] for s in type_stats.values())} 个独立实体")

if __name__ == '__main__':
    main()

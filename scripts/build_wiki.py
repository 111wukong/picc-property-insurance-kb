#!/usr/bin/env python3
"""保险概念 Wiki 词条生成器"""
from pathlib import Path
from html import escape

WIKI_DIR = Path("/Users/wukong/Desktop/龙虾场/picc-property-insurance-kb/docs/concepts")
WIKI_DIR.mkdir(parents=True, exist_ok=True)

CSS = """<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC','Microsoft YaHei','Noto Serif SC',sans-serif; background: #FAFBFC; color: #1A1A2E; line-height: 1.9; padding: 40px 24px; }
  .container { max-width: 780px; margin: 0 auto; }
  .breadcrumb { font-size: 13px; color: #5A6178; margin-bottom: 24px; }
  .breadcrumb a { color: #1D39C4; text-decoration: none; }
  h1 { font-size: 28px; font-weight: 900; color: #D4380D; margin-bottom: 8px; }
  .tag { display: inline-block; background: #D4380D11; color: #D4380D; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-bottom: 16px; }
  .def { background: linear-gradient(135deg,#FFF7E6,#FFFBE6); border-left: 4px solid #FAAD14; padding: 16px 20px; border-radius: 4px; margin: 20px 0; font-size: 16px; }
  .legal { background: #F0F5FF; border-left: 4px solid #1D39C4; padding: 12px 16px; margin: 16px 0; font-size: 14px; color: #1D39C4; border-radius: 4px; }
  h2 { font-size: 20px; font-weight: 700; color: #1D39C4; margin: 32px 0 12px; padding-left: 12px; border-left: 4px solid #1D39C4; }
  h3 { font-size: 16px; font-weight: 600; color: #531DAB; margin: 20px 0 8px; }
  ul { padding-left: 24px; }
  li { margin: 6px 0; }
  .formula { background: #1A1A2E; color: #22C55E; font-family: 'SF Mono','Consolas',monospace; padding: 12px 20px; border-radius: 6px; margin: 12px 0; font-size: 15px; text-align: center; }
  .note { background: #FFF2F0; border: 1px solid #FFCCC7; padding: 12px 16px; border-radius: 6px; margin: 16px 0; font-size: 14px; }
  .related { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
  .related a { padding: 4px 12px; background: #F0F2F5; color: #1D39C4; text-decoration: none; border-radius: 16px; font-size: 13px; }
  .related a:hover { background: #D6E4FF; }
  .footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid #E8ECF1; font-size: 12px; color: #8C8C8C; }
  @media (max-width: 768px) { body { padding: 20px 14px; } h1 { font-size: 22px; } }
</style>"""

def make_page(title, slug, category, definition, legal=None, key_points=None, items=None, formula=None, note=None, related=None, example_text=None):
    body = f"""<div class="container">
  <div class="breadcrumb"><a href="../index.html">PICC企财险知识库</a> › <a href="concepts/index.html">概念词条</a> › {title}</div>
  <span class="tag">{category}</span>
  <h1>{title}</h1>
  <div class="def">{definition}</div>"""
    if legal:
        body += f'\n  <div class="legal">📜 {legal}</div>'
    body += '\n  <h2>核心要点</h2>\n  <ul>'
    if key_points:
        for kp in key_points:
            body += f'\n    <li>{kp}</li>'
    body += '\n  </ul>'
    if formula:
        body += f'\n  <div class="formula">{formula}</div>'
    if items:
        for label, item_list in items:
            body += f'\n  <h3>{label}</h3>\n  <ul>'
            for item in item_list:
                if isinstance(item, tuple):
                    body += f'\n    <li><strong>{item[0]}</strong>：{item[1]}</li>'
                else:
                    body += f'\n    <li>{item}</li>'
            body += '\n  </ul>'
    if example_text:
        body += f'\n  <h3>示例</h3>\n  <ul>'
        for ex in example_text:
            body += f'\n    <li>{ex}</li>'
        body += '\n  </ul>'
    if note:
        body += f'\n  <div class="note"><strong>⚠️ 重要提示：</strong>{note}</div>'
    if related:
        body += '\n  <h3>相关概念</h3>\n  <div class="related">'
        for r in related:
            body += f'\n    <a href="#">{r}</a>'
        body += '\n  </div>'
    body += f'\n  <div class="footer"><p>PICC企财险知识库 · <a href="../index.html">返回首页</a> · <a href="concepts/index.html">全部词条</a></p><p style="margin-top:4px;">仅供学术研究参考，具体以保险合同为准。</p></div>\n</div>'
    html = f'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>{title} — PICC企财险知识库</title>\n{CSS}\n</head>\n<body>\n{body}\n</body>\n</html>'
    (WIKI_DIR / f"{slug}.html").write_text(html, encoding='utf-8')
    print(f"  ✅ {title}")

# 10个核心词条
make_page("保险标的", "insurance-subject", "保险核心概念",
    "保险标的，亦称\"保险对象\"，是保险合同双方当事人权利义务所指向的对象，即保险人承担保险责任所对应的财产、有关利益或责任。",
    "《保险法》第十二条：财产保险的被保险人在保险事故发生时，对保险标的应当具有保险利益。",
    ["保险标的必须具有保险利益——投保人或被保险人对保险标的具有法律上承认的经济利害关系",
     "保险标的的价值是确定保险金额的基础，直接影响赔偿计算",
     "保险标的的范围由保险合同明确约定，不在约定范围内的财产不属于保险标的",
     "保险标的的存放地址应在保险合同中载明，地址变更需及时通知保险人"],
    [("常见类型", [("建筑物","房屋、厂房、仓库等固定资产，通常以重置价值确定保险价值"),
                  ("机器设备","生产设备、动力设备、传导设备等，可单独或整体投保"),
                  ("存货","原材料、在产品、半成品、产成品、商品等流动资产"),
                  ("在建工程","正在施工的建筑工程，需特别约定方可承保"),
                  ("办公用品","家具、计算机、打印机等低值易耗品")]),
     ("不可保财产", ["金银珠宝、钻石玉器、古玩字画等珍贵财物","土地、矿藏、水资源等自然资源",
                  "货币、票证、有价证券","文件、账册、计算机数据等无法鉴定价值的财产",
                  "枪支弹药、违章建筑、非法占用财产","领取公共行驶执照的机动车辆","动植物、农作物"])],
    related=["保险金额","保险价值","重置价值","保险利益"]
)

make_page("保险金额", "sum-insured", "保险核心概念",
    "保险金额，简称\"保额\"，是保险人承担赔偿保险金责任的最高限额，也是计算保险费的依据。",
    "保险金额由投保人参照保险价值自行确定，超过保险价值的部分无效。",
    ["保险金额是赔偿上限，实际赔偿金额不超过保险金额",
     "保险金额与保险价值的比例决定是否足额投保",
     "不足额投保将导致比例赔偿：赔偿 = 损失 × (保险金额/保险价值)",
     "超额投保部分无效，保险人仅按保险价值承担赔偿责任"],
    [("确定方式", [("重置价值","重新建造/购置相同财产的全部费用，适用于固定资产"),
                  ("账面余额","企业会计账簿记载的资产净值，适用于存货"),
                  ("市场价值","公开市场上出售财产可获得的价款"),
                  ("协商价值","投保人与保险人协商确定的其他标准")])],
    related=["保险价值","保险标的","免赔额","比例赔偿"]
)

make_page("免赔额", "deductible", "保险核心概念",
    "免赔额是保险合同中约定的，由被保险人自行承担的损失金额。保险人对超过免赔额的部分承担赔偿责任。",
    key_points=["设置目的：减少小额索赔、降低费率、激励被保险人加强风险管控",
     "绝对免赔额：无论损失大小，被保险人先自担免赔额，保险人赔偿超出部分",
     "免赔率：以损失金额的百分比计算，如\"损失金额的5%，最低500元\"",
     "企财险通常适用每次事故免赔额（非累计免赔额）"],
    example_text=["绝对免赔额500元：损失300元→不赔，损失800元→赔300元",
                "免赔率5%+最低500元：损失8,000元→扣400但不足500→扣500元，赔7,500元"],
    related=["保险金额","赔偿处理","保险费率"]
)

make_page("重置价值", "replacement-value", "保险核心概念",
    "重置价值是指重新建造、购置或安装与被保险财产相同或类似的全新财产所需支付的费用，包含运费、安装费、关税等。",
    key_points=["重置价值是企财险最常用的保险价值确定方式",
     "按重置价值投保可获得足额保障，全损时按重置价值赔偿",
     "旧财产按原样修复即可的，不要求全新重置",
     "重置价值应包含合理的运输费、安装费、关税和增值税"],
    related=["保险价值","保险金额","保险标的"]
)

make_page("责任免除", "exclusion", "保险核心概念",
    "责任免除，亦称除外责任，是保险合同中约定的保险人不承担赔偿责任的损失、费用或情形。",
    key_points=["责任免除是保险合同的核心条款，直接影响保障范围",
     "法定免责 vs 约定免责：法律规定+双方协商约定",
     "举证责任：主张免责的保险人负有举证责任",
     "责任免除条款应以显著方式说明，未说明的不产生效力"],
    items=[("常见免责事项", ["被保险人故意行为、重大过失","战争、军事行动、武装冲突",
     "核辐射、核爆炸、核污染","地震、海啸及其次生灾害",
     "保险标的自然磨损、内在缺陷、自燃","行政行为或司法行为"])],
    related=["保险责任","保险标的","投保人义务"]
)

make_page("比例赔偿", "proportionate-indemnity", "保险核心概念",
    "比例赔偿是企财险的基本赔偿方式。当保险金额低于保险价值时（不足额投保），赔偿金额按保险金额与保险价值的比例计算。",
    formula="赔偿金额 = 实际损失 × (保险金额 / 出险时保险价值)",
    key_points=["比例赔偿仅适用于不足额投保",
     "保险金额≥保险价值时，按实际损失赔偿（最高不超保险价值）",
     "这是保险法\"按比例承担\"原则的具体体现",
     "确定保险价值的时点通常为\"出险时\"，而非投保时"],
    example_text=["厂房重置价值200万，投保100万（不足额）。火灾损失50万→赔偿25万，自担25万"],
    related=["保险金额","保险价值","赔偿处理","免赔额"]
)

make_page("财产基本险", "basic-property", "险种解读",
    "财产基本险是企财险中最基础的主险产品，承保火灾、爆炸、雷击及飞行物体坠落三项核心风险，是所有企财险产品的起点。",
    key_points=["承保：火灾、爆炸、雷击、飞行物体坠落",
     "不保：暴雨、洪水、台风等自然灾害",
     "不保：盗窃、抢劫","不保：水箱水管爆裂"],
    items=[("覆盖递进", ["财产基本险 → 财产综合险（扩展自然灾害）→ 财产一切险（扩展意外事故+盗窃）"])],
    note="财产基本险是\"指定风险\"承保方式——仅承保明确列出的风险，未列明的不赔。",
    related=["财产综合险","财产一切险","保险责任","责任免除"]
)

make_page("财产一切险", "all-risk-property", "险种解读",
    "财产一切险是企财险中覆盖面最广的主险产品，承保保险单中列明的除外责任以外的一切自然灾害和意外事故造成的保险标的损失。",
    key_points=["承保范围最广：除列明除外责任外，一切突发意外事故均保",
     "\"一切险减除外\"承保方式——举证责任倒置，保险人须证明属除外责任才能拒赔",
     "包含：火灾/爆炸/雷击/自然灾害/盗窃/水箱爆裂/其他意外事故",
     "不保：地震/海啸/战争/核辐射/自然磨损"],
    note="财产一切险并非\"什么都赔\"。除外责任（地震、战争等）仍然不保。但它的承保逻辑是\"除非明确除外，否则都赔\"，与基本险的\"除非明确列明，否则不赔\"相反。",
    related=["财产基本险","财产综合险","保险责任","责任免除"]
)

make_page("投保人", "policyholder", "合同主体",
    "投保人是与保险人订立保险合同，并按照合同约定负有支付保险费义务的人。投保人可以是自然人、法人或其他组织。",
    key_points=["投保人必须对保险标的具有保险利益",
     "投保人负有如实告知义务——对保险人询问应如实回答",
     "投保人应按照约定及时足额支付保险费",
     "投保人可以是被保险人本人，也可以是为他人利益投保的第三人",
     "投保人有权随时解除保险合同（另有约定除外）"],
    related=["保险人","被保险人","保险利益","如实告知义务"]
)

make_page("被保险人", "insured", "合同主体",
    "被保险人是其财产或者人身受保险合同保障，享有保险金请求权的人。投保人可以是被保险人。",
    key_points=["被保险人是保险事故发生时享有赔偿请求权的主体",
     "被保险人负有出险通知义务和施救减损义务",
     "被保险人应维护保险标的安全，遵守安全生产法规",
     "被保险人转让保险标的应通知保险人"],
    related=["投保人","保险人","保险标的","赔偿处理"]
)

# 索引页
cards = []
CONCEPTS = [
    ("insurance-subject","保险标的","保险核心概念"),
    ("sum-insured","保险金额","保险核心概念"),
    ("deductible","免赔额","保险核心概念"),
    ("replacement-value","重置价值","保险核心概念"),
    ("exclusion","责任免除","保险核心概念"),
    ("proportionate-indemnity","比例赔偿","保险核心概念"),
    ("basic-property","财产基本险","险种解读"),
    ("all-risk-property","财产一切险","险种解读"),
    ("policyholder","投保人","合同主体"),
    ("insured","被保险人","合同主体"),
]
for slug, title, cat in CONCEPTS:
    cards.append(f'<a href="{slug}.html" class="card"><span class="cat">{cat}</span><h3>{title}</h3></a>')

idx_html = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>概念词条 — PICC企财险知识库</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;background:#FAFBFC;color:#1A1A2E;padding:40px 24px}}
.container{{max-width:800px;margin:0 auto}}
.breadcrumb{{font-size:13px;color:#5A6178;margin-bottom:24px}}
.breadcrumb a{{color:#1D39C4;text-decoration:none}}
h1{{font-size:28px;font-weight:900;color:#D4380D;margin-bottom:8px}}
.subtitle{{color:#5A6178;font-size:14px;margin-bottom:28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px}}
.card{{display:block;background:white;border:1px solid #E8ECF1;border-radius:8px;padding:16px 20px;text-decoration:none;color:inherit;transition:all .2s}}
.card:hover{{border-color:#D4380D;box-shadow:0 2px 12px rgba(212,56,13,.08);transform:translateY(-1px)}}
.cat{{display:inline-block;background:#F0F2F5;color:#5A6178;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;margin-bottom:8px}}
.card h3{{font-size:16px;font-weight:700}}
.footer{{margin-top:40px;padding-top:16px;border-top:1px solid #E8ECF1;font-size:12px;color:#8C8C8C}}
.footer a{{color:#1D39C4}}
</style></head><body><div class="container">
<div class="breadcrumb"><a href="../index.html">PICC企财险知识库</a> › 概念词条</div>
<h1>📚 保险概念词条</h1><p class="subtitle">{len(CONCEPTS)} 个核心保险概念深度解读</p>
<div class="grid">{''.join(cards)}</div>
<div class="footer"><p>PICC企财险知识库 · <a href="../index.html">返回首页</a></p></div>
</div></body></html>'''
(WIKI_DIR / "index.html").write_text(idx_html, encoding='utf-8')
print(f"\n📊 共 {len(CONCEPTS)} 个词条 + 索引页")

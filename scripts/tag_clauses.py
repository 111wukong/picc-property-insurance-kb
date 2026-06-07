#!/usr/bin/env python3
"""
PICC企财险知识库 — AI 标注管线
使用 DeepSeek API 对条款正文进行实体标注，输出 tagged.md

标注体系（23 类实体，详见 ontology/entity-types.json）：

条款结构（8类）：
  〖@险种名〗 〖§章节〗 〖¶条目〗 〖№备案号〗 〖+附加险〗 〖≡特别约定〗 〖↗版本引用〗

保险核心概念（10类）：
  〖☐保险标的〗 〖⚡保险责任〗 〖✕责任免除〗 〖$保险金额〗 〖%免赔额〗
  〖⏱保险期间〗 〖¥费率〗 〖⛓赔偿处理〗 〖◈义务条款〗 〖⚖定义条款〗

合同主体与单据（5类）：
  〖▶投保人〗 〖◀保险人〗 〖◆被保险人〗 〖📋合同单据〗 〖▣第三方〗

标注规则：
1. 只标注明确属于该类型的术语/短语，不要过度标注
2. 实体标注包裹在原文中，不改变原文顺序
3. 同一段落内同一实体多次出现都要标注
4. 章节标题（总则、保险责任等）标注为〖§章节〗
5. 条文编号（第一条、第二条等）标注为〖¶条目〗
6. 险种名称（财产基本险等）标注为〖@险种名〗
7. 火灾、爆炸、雷击等具体风险标注为〖⚡保险责任〗
8. 地震、战争等除外风险标注为〖✕责任免除〗
9. 建筑物、机器设备等承保财产标注为〖☐保险标的〗
10. 如实告知、及时通知等义务标注为〖◈义务条款〗
"""
import os
import sys
import json
import time
from pathlib import Path
from openai import OpenAI

# ====================== 配置 ======================
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_BASE = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com")

CORPUS_DIR = Path.home() / "Desktop/龙虾场/picc-property-insurance-kb/corpus"
TAGGED_DIR = Path.home() / "Desktop/龙虾场/picc-property-insurance-kb/tagged"

# ====================== 标注 Prompt ======================
SYSTEM_PROMPT = """你是一位专业的保险条款标注专家。你的任务是对 PICC 企财险条款正文进行实体标注。

## 标注语法
使用 〖MARKER 实体文本〗 格式将实体包裹在原文中。MARKER 是单字符标记符号。

## 实体类型定义

### 条款结构（8类）
- 〖@险种名〗 — 保险产品名称（如：财产基本险、机器损坏保险）
- 〖§章节〗 — 条款章节标题（如：总则、保险责任、责任免除、赔偿处理）
- 〖¶条目〗 — 条款编号（如：第一条、第三条、第八条第（二）款）
- 〖№备案号〗 — 监管备案编号
- 〖+附加险〗 — 附加险条款名称
- 〖≡特别约定〗 — 特别约定条款/内容
- 〖↗版本引用〗 — 条款版本引用

### 保险核心概念（10类）
- 〖☐保险标的〗 — 被承保的财产（如：建筑物、机器设备、存货、在建工程）
- 〖⚡保险责任〗 — 承保的风险/事故（如：火灾、爆炸、雷击、飞行物体坠落）
- 〖✕责任免除〗 — 不保的风险/情形（如：地震、战争、核辐射、故意行为）
- 〖$保险金额〗 — 保险金额/保险价值约定（如：出险时重置价值、账面余额、市场价值）
- 〖%免赔额〗 — 免赔额/免赔率约定
- 〖⏱保险期间〗 — 保险期限约定（如：一年、以保险单载明为准）
- 〖¥费率〗 — 保险费率相关内容
- 〖⛓赔偿处理〗 — 理赔计算方式（如：比例赔偿、第一危险赔偿、货币赔偿）
- 〖◈义务条款〗 — 合同义务（如：如实告知、及时通知、施救义务）
- 〖⚖定义条款〗 — 术语法定定义（如：重大过失、恐怖活动、重置价值）

### 合同主体与单据（5类）
- 〖▶投保人〗 — 投保主体（如：财产所有人、共有人、承租人）
- 〖◀保险人〗 — 保险公司
- 〖◆被保险人〗 — 被保险主体
- 〖📋合同单据〗 — 合同相关文件（如：投保单、保险单、批单、保险凭证）
- 〖▣第三方〗 — 合同外相关方（如：公估人、受益人、代理人）

## 标注规则
1. 保持原文完整，只在实体周围添加标注标记
2. 同一实体在文中多次出现都要标注
3. 标注要精准——只标注明确的实体，不过度标注
4. 章节标题必然标注为〖§章节〗
5. 条文序号必然标注为〖¶条目〗
6. 输出格式：直接输出标注后的纯文本，用 Markdown 标题标记章节，不要添加任何解释说明
7. 使用 # 标记险种标题，## 标记章节标题
8. 每个段落之间用空行分隔
"""

USER_PROMPT_TEMPLATE = """请对以下保险条款正文进行实体标注。直接输出标注后的 tagged.md 格式文本，不要添加任何解释。

险种信息：
- 产品名称：{product_name}
- 条款标题：{clause_title}

条款正文：
---
{clause_text}
---"""

# ====================== 标注函数 ======================
def annotate_clause(product_name, clause_title, clause_text):
    """调用 DeepSeek API 进行实体标注"""
    client = OpenAI(api_key=API_KEY, base_url=API_BASE)

    # 截断过长文本（防止 token 超限）
    max_chars = 15000
    if len(clause_text) > max_chars:
        clause_text = clause_text[:max_chars] + "\n\n[文本过长，已截断]"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        product_name=product_name,
        clause_title=clause_title,
        clause_text=clause_text
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # 低温度保证一致性
            max_tokens=16000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  ❌ API 调用失败: {e}")
        return None

def process_product(meta_path):
    """处理单个险种"""
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    product_name = meta['product_name']
    product_id = meta['product_id']
    clause_title = meta['title']

    # 读取条款正文
    txt_path = meta_path.parent / "条款正文.txt"
    if not txt_path.exists():
        print(f"  ⚠️ 未找到正文: {txt_path}")
        return None

    clause_text = txt_path.read_text(encoding='utf-8')

    print(f"\n🏷️ [{product_id}] {product_name}")
    print(f"   原文: {len(clause_text)} 字符")

    # 调用 AI 标注
    tagged = annotate_clause(product_name, clause_title, clause_text)

    if tagged is None:
        return None

    # 保存 tagged.md
    safe_name = product_name.replace('/', '_').replace('\\', '_')
    tagged_path = TAGGED_DIR / f"{product_id}_{safe_name}.tagged.md"
    tagged_path.write_text(tagged, encoding='utf-8')

    # 统计标注数量
    import re
    entity_count = len(re.findall(r'〖[^〗]+〗', tagged))

    print(f"   标注: {entity_count} 处实体")
    print(f"   输出: {tagged_path}")

    return {
        'product_id': product_id,
        'product_name': product_name,
        'tagged_path': str(tagged_path),
        'entity_count': entity_count,
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI 标注条款')
    parser.add_argument('--product', type=str, help='指定险种编号（如 1,2,3），不指定则全部')
    parser.add_argument('--limit', type=int, default=0, help='限制标注数量（0=全部）')
    parser.add_argument('--delay', type=float, default=2.0, help='API 调用间隔（秒）')
    args = parser.parse_args()

    TAGGED_DIR.mkdir(parents=True, exist_ok=True)

    # 收集产品
    products = []
    for meta_path in sorted(CORPUS_DIR.glob("*/meta.json")):
        if args.product:
            product_num = meta_path.parent.name.split('_')[0]
            if product_num not in args.product.split(','):
                continue
        products.append(meta_path)

    if args.limit > 0:
        products = products[:args.limit]

    print(f"📊 待标注: {len(products)} 个险种")
    print(f"   模型: {MODEL}")
    print(f"   API: {API_BASE}")

    results = []
    for i, meta_path in enumerate(products):
        result = process_product(meta_path)
        if result:
            results.append(result)

        # 延迟避免限流
        if i < len(products) - 1:
            time.sleep(args.delay)

    # 汇总
    total_entities = sum(r['entity_count'] for r in results if r)
    print(f"\n{'='*60}")
    print(f"✅ 标注完成: {len(results)}/{len(products)} 成功")
    print(f"   总实体标注: {total_entities} 处")

if __name__ == '__main__':
    main()

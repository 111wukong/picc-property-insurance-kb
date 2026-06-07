#!/usr/bin/env python3
"""
知识图谱构建器 — 从 tagged.md 和产品元数据中提取关系网络
"""
import re
import json
from pathlib import Path
from collections import defaultdict

TAGGED_DIR = Path("/Users/wukong/Desktop/龙虾场/picc-property-insurance-kb/tagged")
CORPUS_DIR = Path("/Users/wukong/Desktop/龙虾场/picc-property-insurance-kb/corpus")
KG_DIR = Path("/Users/wukong/Desktop/龙虾场/picc-property-insurance-kb/kg")

# 险种分类映射
PRODUCT_TAXONOMY = {
    "财产基本险": {"parent": None, "category": "财产险主险", "level": 1},
    "财产综合险": {"parent": "财产基本险", "category": "财产险主险", "level": 2,
                "extends": ["暴雨", "洪水", "暴风", "龙卷风", "冰雹", "台风", "飓风", "暴雪", "冰凌", "沙尘暴", "滑坡", "泥石流", "地面下陷"]},
    "财产一切险": {"parent": "财产综合险", "category": "财产险主险", "level": 3,
               "extends": ["水箱水管爆裂", "盗窃抢劫", "其他突然意外事故"]},
    "机损险": {"parent": "财产一切险", "category": "财产险主险", "level": 2,
              "note": "独立主险，通常与财产险搭配"},
    "营业中断保险": {"parent": None, "category": "利润损失险", "level": 1,
                 "note": "依附于财产险/机损险"},
    "现金保险": {"parent": None, "category": "特殊财产险", "level": 1},
    "高新技术企业财产一切险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "高新技术企业财产综合险": {"parent": "财产综合险", "category": "行业定制险", "level": 3},
    "计算机硬件及费用损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "珠宝商财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "风电企业运营期财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "变压器财产损失保险": {"parent": "机损险", "category": "行业定制险", "level": 3},
    "锅炉压力容器财产损失保险": {"parent": "机损险", "category": "行业定制险", "level": 3},
    "工程机械设备财产损失保险": {"parent": "机损险", "category": "行业定制险", "level": 3},
    "机器人财产损失保险": {"parent": "机损险", "category": "行业定制险", "level": 3},
    "智能网联设备财产损失保险": {"parent": "机损险", "category": "行业定制险", "level": 3},
    "光伏电站运营期财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "机场资产定制财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "恐怖袭击财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "文化体育产业财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "仓单财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "观赏动物饲养馆财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "住宅共用部位财产损失保险": {"parent": "财产基本险", "category": "行业定制险", "level": 3},
    "房屋整体倒塌财产损失保险": {"parent": "财产基本险", "category": "行业定制险", "level": 3},
    "北京市巨灾财产损失保险": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "起重机械财产损失保险": {"parent": "机损险", "category": "行业定制险", "level": 3},
    "商业燃气火灾爆炸泄漏": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "商业燃气用户": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "工业燃气火灾爆炸泄漏": {"parent": "财产一切险", "category": "行业定制险", "level": 3},
    "高新技术企业关键研发设备损失保险": {"parent": "机损险", "category": "行业定制险", "level": 3},
    "高新技术企业研发中断费用保险": {"parent": "营业中断保险", "category": "行业定制险", "level": 3},
}

# 保险责任覆盖（从 tagged 中提取各险种标注的 ⚡ 保险责任实体）
def extract_perils():
    """提取各产品的承保风险"""
    peril_map = defaultdict(set)
    
    for md_file in sorted(TAGGED_DIR.glob("*.md")):
        product_name = md_file.stem
        text = md_file.read_text(encoding='utf-8')
        
        # 提取 ⚡ 标注（保险责任）
        perils = re.findall(r'〖⚡([^〗]+)〗', text)
        for p in perils:
            p = p.strip()
            if len(p) >= 2 and len(p) <= 20:  # 过滤过长/过短的
                peril_map[product_name].add(p)
    
    return peril_map

def extract_named_product(text_snippet):
    """从 tagged 文本片段中识别产品名"""
    # 匹配 @ 标注
    products = re.findall(r'〖@([^〗]+)〗', text_snippet)
    if products:
        return products[0].strip()
    return None

def build_knowledge_graph():
    """构建完整知识图谱"""
    KG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. 产品关系网络
    with open(CORPUS_DIR / 'index.json', 'r') as f:
        products_data = json.load(f)
    
    nodes = []
    links = []
    node_ids = {}
    
    for i, p in enumerate(products_data['products']):
        name = p['product_name']
        pid = p['product_id']
        node_id = f"p{pid}"
        node_ids[name] = node_id
        
        # 匹配分类
        category = "其他险种"
        parent = None
        for key, info in PRODUCT_TAXONOMY.items():
            if key in name:
                category = info['category']
                parent = info.get('parent')
                break
        
        nodes.append({
            "id": node_id,
            "name": name[:30],
            "fullName": name,
            "category": category,
            "chars": p['char_count'],
            "articles": p['article_count'],
            "groupId": {"财产险主险": 1, "利润损失险": 2, "特殊财产险": 3, "行业定制险": 4}.get(category, 5),
        })
        
        # 建立继承关系
        if parent:
            for pname, pid2 in node_ids.items():
                if parent in pname:
                    links.append({
                        "source": node_id,
                        "target": pid2,
                        "type": "extends",
                        "label": "特化/扩展"
                    })
                    break
    
    # 手动添加关键关系
    extra_links = [
        # 三联关系：基本→综合→一切
        {"source": "p2", "target": "p1", "type": "extends", "label": "扩展覆盖"},
        {"source": "p3", "target": "p2", "type": "extends", "label": "扩展覆盖"},
        {"source": "p5", "target": "p1", "type": "companion", "label": "搭配主险"},
        {"source": "p7", "target": "p1", "type": "depends_on", "label": "依附财产险"},
    ]
    links.extend(extra_links)
    
    # 2. 保险责任覆盖矩阵
    peril_map = extract_perils()
    
    # 取所有出现过的风险
    all_perils = set()
    for perils in peril_map.values():
        all_perils.update(perils)
    
    # 过滤：只保留关键风险（出现在3个以上险种中或长度合适）
    peril_freq = defaultdict(int)
    for perils in peril_map.values():
        for p in perils:
            peril_freq[p] += 1
    
    key_perils = sorted(
        [p for p, f in peril_freq.items() if f >= 2 and len(p) <= 15],
        key=lambda p: peril_freq[p], reverse=True
    )[:30]
    
    coverage_matrix = {
        "products": [p['product_name'][:25] for p in products_data['products']],
        "perils": key_perils,
        "matrix": []
    }
    
    for p in products_data['products']:
        name = p['product_name']
        # 找匹配的 tagged 文件
        row = []
        product_perils = set()
        pid = p['product_id']
        tagged_files = list(TAGGED_DIR.glob(f"{pid}_*.md"))
        if tagged_files:
            text = tagged_files[0].read_text(encoding='utf-8')
            product_perils = set(re.findall(r'〖⚡([^〗]+)〗', text))
        
        for peril in key_perils:
            row.append(1 if any(peril in pp for pp in product_perils) else 0)
        coverage_matrix["matrix"].append(row)
    
    # 保存
    graph_data = {"nodes": nodes, "links": links}
    (KG_DIR / "product_graph.json").write_text(
        json.dumps(graph_data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    (KG_DIR / "coverage_matrix.json").write_text(
        json.dumps(coverage_matrix, ensure_ascii=False, indent=2), encoding='utf-8')
    
    (KG_DIR / "index.json").write_text(json.dumps({
        "node_count": len(nodes),
        "link_count": len(links),
        "peril_count": len(key_perils),
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"✅ 知识图谱构建完成")
    print(f"   节点: {len(nodes)} | 关系: {len(links)}")
    print(f"   风险覆盖: {len(key_perils)} 个关键风险 × {len(products_data['products'])} 个险种")
    
    return graph_data, coverage_matrix

if __name__ == '__main__':
    graph, matrix = build_knowledge_graph()

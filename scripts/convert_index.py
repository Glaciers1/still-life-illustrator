#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_index.py —— 旬物索引 MD → JSON 数据库转换工具。

把 references/seasonal-produce-index.md 解析为结构化 JSON（seasonal_produce_index.json），
包含每个条目的 name/category/season/固有色/质感/结构/成熟/搭配等字段。

MD 保留为人类可读 SSOT（单一事实来源），JSON 由 MD 自动生成，供脚本快速查询。
self_skeleton.py 和 director_dom.py 优先 json.load() 读取 JSON，不存在时回退 MD。

用法:
  python convert_index.py
  python convert_index.py --md <md路径> --out <json路径>
  python convert_index.py --verify  # 只验证解析结果，不写文件
"""
import json
import os
import re
import sys
import argparse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.normpath(os.path.join(HERE, ".."))
DEFAULT_MD = os.path.join(SKILL_ROOT, "references", "seasonal-produce-index.md")
DEFAULT_JSON = os.path.join(SKILL_ROOT, "references", "seasonal_produce_index.json")

# 类别关键词映射（与 director_dom.py 保持一致）
_COMMON_FRUITS = {
    "草莓", "番茄", "苹果", "梨", "桃", "葡萄", "西瓜", "芒果", "菠萝", "香蕉",
    "橙子", "柠檬", "柚子", "橘子", "柿子", "石榴", "无花果", "猕猴桃", "樱桃",
    "李子", "杏", "枣", "蓝莓", "树莓", "蔓越莓", "荔枝", "龙眼", "杨梅", "枇杷",
    "山楂", "百香果", "火龙果", "牛油果", "椰子", "榴莲", "山竹", "木瓜", "杨桃",
    "橄榄", "白果", "莲子", "荸荠", "芋艿", "山药", "土豆", "红薯", "紫薯",
}

_CATEGORY_KEYWORDS = {
    "seafood": ["鱼", "虾", "蟹", "贝", "蚝", "蛤", "蛏", "鱿", "墨", "章", "鲍", "参",
                "翅", "肚", "裙带", "海带", "紫菜", "海蜇", "青花鱼", "三文鱼", "金枪鱼",
                "鳕鱼", "鲈鱼", "带鱼", "黄鱼", "鲳鱼", "鳗鱼", "章鱼", "墨鱼", "鱿鱼",
                "对虾", "基围虾", "斑节虾", "小龙虾", "皮皮虾", "帝王蟹", "梭子蟹", "青蟹",
                "大闸蟹", "花蟹", "生蚝", "牡蛎", "花蛤", "文蛤", "北极贝", "扇贝", "鲍鱼",
                "海参", "海胆", "海螺", "蛏子", "蚬子"],
    "dessert": ["蛋糕", "饼干", "面包", "酥", "挞", "派", "布丁", "果冻", "慕斯", "冰淇淋",
                "巧克力", "糖果", "马卡龙", "可露丽", "玛德琳", "达克瓦兹", "千层", "铜锣烧",
                "大福", "曲奇", "蛋白霜", "蜂蜜蛋糕", "磅蛋糕", "镜面蛋糕", "戚风", "巴斯克",
                "提拉米苏", "舒芙蕾", "华夫饼", "松饼", "司康", "贝果", "碱水", "法棍",
                "吐司", "可颂", "丹麦", "泡芙", "蛋挞", "椰丝", "牛轧糖", "太妃糖"],
    "vegetable": ["芦笋", "豌豆", "洋蓟", "春笋", "香椿", "莴笋", "春韭", "荠菜", "番茄",
                  "黄瓜", "茄子", "辣椒", "莲藕", "茭白", "茨菇", "木耳", "香菇", "平菇",
                  "杏鲍菇", "羊肚菌", "牛肝菌", "松露", "竹荪", "银耳", "百合", "芡实",
                  "菱角", "茨实", "秋葵", "芹菜", "菠菜", "白菜", "甘蓝", "花椰菜", "西兰花",
                  "萝卜", "胡萝卜", "洋葱", "大蒜", "姜", "葱", "香菜", "薄荷", "罗勒",
                  "迷迭香", "百里香", "牛至", "鼠尾草", "薰衣草", "洋甘菊"],
    "flower": ["郁金香", "牡丹", "紫藤", "樱花", "金莲花", "风信子", "月季", "洋牡丹",
               "康乃馨", "鸢尾", "紫罗兰", "马蹄莲", "泡泡玫瑰", "食用花", "荷花", "菊花",
               "桂花", "梅花", "兰花", "百合", "向日葵", "玫瑰", "满天星", "尤加利",
               "银叶菊", "绣球", "茉莉", "栀子", "含笑", "玉兰", "海棠", "丁香"],
    "utensil": ["刀", "叉", "勺", "杯", "碗", "盘", "碟", "壶", "瓶", "罐", "锅",
                "砧板", "托盘", "蒸笼", "茶盘", "花瓶", "餐巾", "餐布", "书籍", "画框",
                "筷子", "筷架", "量杯", "油瓶", "酱油碟", "饭勺", "茶滤", "茶托",
                "茶盏", "茶杯", "汤锅", "手冲", "咖啡壶", "餐盘", "银质", "铜质",
                "不锈钢", "陶瓷", "玻璃", "木质", "竹制", "石臼", "木托盘"],
    "grain": ["米", "面", "麦", "稻", "粟", "黍", "稷", "粱", "玉米", "燕麦", "荞麦",
              "藜麦", "黑米", "红米", "糙米", "糯米", "小米", "薏米", "芡实", "莲子",
              "红豆", "绿豆", "黄豆", "黑豆", "芸豆", "扁豆", "豌豆", "蚕豆"],
    "dairy": ["牛奶", "黄油", "奶酪", "芝士", "酸奶", "奶油", "炼乳", "奶粉", "羊奶",
              "马苏里拉", "帕玛森", "布里", "蓝纹", "车达", "奶油奶酪"],
}


def classify_subject(name):
    """根据条目名称推断类别。"""
    if not name:
        return "other"
    if name in _COMMON_FRUITS:
        return "fruit"
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return cat
    return "other"


def parse_index(md_path):
    """解析旬物索引 MD，返回条目列表。"""
    with open(md_path, "r", encoding="utf-8-sig") as f:
        text = f.read()

    items = []
    current_season = None

    # 按行处理，跟踪当前季节分区（## 春/夏/秋/冬/全年·常备 共五区；季节字后须紧跟空白/·/（/行尾，故『## 秋葵』这类以季节字开头的 H2 条目不误判）
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # 检测季节标题
        season_match = re.match(r'^##\s+(春|夏|秋|冬|全年)(?=[\s·（(]|$)', line)
        if season_match:
            current_season = season_match.group(1)
            i += 1
            continue

        # 检测条目标题 ### 名称
        item_match = re.match(r'^###\s+(.+)$', line)
        if item_match:
            name = item_match.group(1).strip()
            # 去掉括号注释
            name = re.sub(r'[（(].*?[）)]', '', name).strip()

            # 下一行是字段内容
            fields_line = ""
            if i + 1 < len(lines):
                fields_line = lines[i + 1].strip()

            # 解析字段：**字段名**：值
            fields = {}
            # 匹配 **字段名**：值（值到下一个 ** 或行尾）
            for m in re.finditer(r'\*\*([^*]+)\*\*[：:]\s*([^*]+?)(?=\*\*|$)', fields_line):
                key = m.group(1).strip()
                value = m.group(2).strip().rstrip("。").strip()
                fields[key] = value

            item = {
                "name": name,
                "category": classify_subject(name),
                "season": current_season or "unknown",
                "固有色": fields.get("固有色", ""),
                "质感": fields.get("质感", ""),
                "结构": fields.get("结构", ""),
                "分布": fields.get("分布", ""),
                "原产": fields.get("原产", ""),
                "成熟": fields.get("成熟", ""),
                "搭配": fields.get("搭配", ""),
                "入画": fields.get("入画", ""),
            }
            items.append(item)
            i += 2
            continue

        i += 1

    return items


def main():
    ap = argparse.ArgumentParser(description="旬物索引 MD → JSON 转换工具")
    ap.add_argument("--md", default=DEFAULT_MD, help="输入 MD 文件路径")
    ap.add_argument("--out", default=DEFAULT_JSON, help="输出 JSON 文件路径")
    ap.add_argument("--verify", action="store_true", help="只验证解析结果，不写文件")
    args = ap.parse_args()

    if not os.path.exists(args.md):
        print(f"错误：MD 文件不存在: {args.md}")
        sys.exit(1)

    items = parse_index(args.md)

    # 统计
    from collections import Counter
    cat_counts = Counter(item["category"] for item in items)
    season_counts = Counter(item["season"] for item in items)

    print(f"===== 旬物索引解析结果 =====")
    print(f"总条目数: {len(items)}")
    print(f"类别分布: {dict(cat_counts)}")
    print(f"季节分布: {dict(season_counts)}")

    # 检查重复
    names = [item["name"] for item in items]
    duplicates = {n: c for n, c in Counter(names).items() if c > 1}
    if duplicates:
        print(f"[警告] 发现重复条目: {duplicates}")
    else:
        print(f"[OK] 无重复条目")

    # 检查字段完整性
    missing_fields = []
    for item in items:
        for field in ("固有色", "质感", "结构", "成熟", "搭配"):
            if not item.get(field):
                missing_fields.append(f"{item['name']}.{field}")
    if missing_fields:
        print(f"[警告] {len(missing_fields)} 个字段缺失: {missing_fields[:10]}{'...' if len(missing_fields) > 10 else ''}")
    else:
        print(f"[OK] 全部字段完整")

    if args.verify:
        print("\n[验证模式] 不写文件。")
        return

    # 写 JSON
    output = {
        "version": "1.0",
        "total": len(items),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_md": os.path.basename(args.md),
        "categories": dict(cat_counts),
        "seasons": dict(season_counts),
        "items": items,
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[完成] JSON 已写入: {args.out}")
    print(f"文件大小: {os.path.getsize(args.out)} bytes")


if __name__ == "__main__":
    main()

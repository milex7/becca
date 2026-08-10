#!/usr/bin/env python3
"""Randomly recommend dinner options from a built-in or custom menu."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import random
import sys
from typing import Sequence


@dataclass(frozen=True)
class Meal:
    """One dinner option and its optional category."""

    category: str | None
    name: str


BUILTIN_MEALS = (
    Meal("米饭", "黄焖鸡米饭"),
    Meal("米饭", "番茄牛腩饭"),
    Meal("米饭", "鱼香肉丝盖饭"),
    Meal("米饭", "咖喱鸡饭"),
    Meal("面食", "兰州牛肉面"),
    Meal("面食", "重庆小面"),
    Meal("面食", "炸酱面"),
    Meal("面食", "意大利肉酱面"),
    Meal("粉类", "螺蛳粉"),
    Meal("粉类", "桂林米粉"),
    Meal("粉类", "炒河粉"),
    Meal("饺子", "鲜肉水饺"),
    Meal("饺子", "锅贴"),
    Meal("快餐", "汉堡薯条"),
    Meal("快餐", "鸡肉卷"),
    Meal("火锅", "麻辣火锅"),
    Meal("火锅", "番茄锅"),
    Meal("烧烤", "烤串"),
    Meal("烧烤", "烤鱼"),
    Meal("轻食", "鸡胸肉沙拉"),
    Meal("轻食", "三文鱼波奇饭"),
    Meal("家常菜", "小炒肉配米饭"),
    Meal("家常菜", "番茄炒蛋配米饭"),
    Meal("家常菜", "麻婆豆腐配米饭"),
    Meal("日韩料理", "石锅拌饭"),
    Meal("日韩料理", "寿司拼盘"),
    Meal("西式", "披萨"),
    Meal("西式", "牛排"),
    Meal("汤饭", "皮蛋瘦肉粥"),
    Meal(None, "便利店饭团"),
)


class MenuError(ValueError):
    """Raised when a menu cannot be used to select dinner."""


def positive_integer(value: str) -> int:
    """Parse a command-line positive integer."""
    try:
        count = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("数量必须是正整数") from error
    if count < 1:
        raise argparse.ArgumentTypeError("数量必须是正整数")
    return count


def _deduplicate(meals: Sequence[Meal]) -> tuple[Meal, ...]:
    seen: set[tuple[str | None, str]] = set()
    unique: list[Meal] = []
    for meal in meals:
        key = (meal.category, meal.name)
        if key not in seen:
            seen.add(key)
            unique.append(meal)
    return tuple(unique)


def load_menu_file(path: Path) -> tuple[Meal, ...]:
    """Read a UTF-8 text menu and retain its first occurrence of each meal."""
    try:
        with path.open(encoding="utf-8-sig") as stream:
            lines = tuple(stream)
    except UnicodeDecodeError as error:
        raise MenuError(f"菜单文件 {path} 不是有效的 UTF-8 编码") from error
    except OSError as error:
        raise MenuError(f"无法读取菜单文件 {path}：{error.strerror or error}") from error

    meals: list[Meal] = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        pipe_count = line.count("|")
        if pipe_count > 1:
            raise MenuError(f"菜单文件 {path} 第 {line_number} 行格式无效：每行只能包含一个“|”")
        if pipe_count == 0:
            meals.append(Meal(None, line))
            continue

        category, name = (field.strip() for field in line.split("|"))
        if not category:
            raise MenuError(f"菜单文件 {path} 第 {line_number} 行格式无效：分类不能为空")
        if not name:
            raise MenuError(f"菜单文件 {path} 第 {line_number} 行格式无效：餐名不能为空")
        meals.append(Meal(category, name))
    return _deduplicate(meals)


def available_categories(meals: Sequence[Meal]) -> tuple[str, ...]:
    """Return categorized meal names in first-appearance order."""
    seen: set[str] = set()
    categories: list[str] = []
    for meal in meals:
        if meal.category is not None and meal.category not in seen:
            seen.add(meal.category)
            categories.append(meal.category)
    return tuple(categories)


def filter_meals(meals: Sequence[Meal], category: str | None) -> tuple[Meal, ...]:
    """Filter meals by an exact, trimmed category when requested."""
    if category is None:
        return tuple(meals)

    selected_category = category.strip()
    filtered = tuple(meal for meal in meals if meal.category == selected_category)
    if filtered:
        return filtered

    categories = available_categories(meals)
    if categories:
        raise MenuError(f"未找到分类“{selected_category}”。可用分类：{'、'.join(categories)}")
    raise MenuError(f"未找到分类“{selected_category}”：菜单中没有已分类的餐食")


def choose_meals(meals: Sequence[Meal], count: int) -> tuple[Meal, ...]:
    """Choose distinct meals without retaining selection history."""
    if count > len(meals):
        raise MenuError(f"请求 {count} 个推荐，但当前只有 {len(meals)} 个可选餐食")
    return tuple(random.sample(meals, count))


def render_text(meals: Sequence[Meal]) -> str:
    """Render recommendations for terminal reading."""
    lines = ["今晚吃什么："]
    lines.extend(
        f"{index}. {meal.name}（{meal.category or '未分类'}）"
        for index, meal in enumerate(meals, start=1)
    )
    return "\n".join(lines)


def render_json(category: str | None, meals: Sequence[Meal]) -> str:
    """Render recommendations as a stable JSON object."""
    return json.dumps(
        {
            "category": category,
            "recommendations": [
                {"name": meal.name, "category": meal.category} for meal in meals
            ],
        },
        ensure_ascii=False,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="随机生成晚餐推荐")
    parser.add_argument("--menu-file", type=Path, metavar="PATH", help="使用 UTF-8 文本菜单替换内置菜单")
    parser.add_argument("--category", metavar="NAME", help="按分类精确筛选")
    parser.add_argument("--count", type=positive_integer, default=3, metavar="N", help="推荐数量（默认：3）")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Run the dinner recommender and return its process status."""
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        meals = load_menu_file(arguments.menu_file) if arguments.menu_file else BUILTIN_MEALS
        category = arguments.category.strip() if arguments.category is not None else None
        recommendations = choose_meals(filter_meals(meals, category), arguments.count)
    except MenuError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2

    if arguments.json:
        print(render_json(category, recommendations))
    else:
        print(render_text(recommendations))
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()

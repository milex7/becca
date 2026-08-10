# 随机晚餐推荐

`scripts/dinner/random_dinner.py` 从内置菜单或自定义菜单中无放回随机选出晚餐建议。仅需要 Python 标准库。

## 运行

macOS 或 Linux：

```bash
python3 scripts/dinner/random_dinner.py
```

Windows PowerShell：

```powershell
py -3 scripts/dinner/random_dinner.py
```

默认输出 3 个推荐：

```text
今晚吃什么：
1. 黄焖鸡米饭（米饭）
2. 螺蛳粉（粉类）
3. 鸡胸肉沙拉（轻食）
```

每次运行独立随机，不保存历史，也不提供随机种子。

## 参数

- `--menu-file PATH`：使用指定的文本菜单，完全替换内置菜单。
- `--category NAME`：按分类精确筛选。分类名会忽略首尾空白，但不进行模糊匹配。
- `--count N`：输出 N 个不重复建议，必须是正整数；默认值为 `3`。
- `--json`：输出 JSON，方便被其他脚本读取。

例如从个人菜单的面食分类中选两项：

```bash
python3 scripts/dinner/random_dinner.py --menu-file dinner.txt --category 面食 --count 2
```

## 自定义菜单格式

菜单文件必须为 UTF-8 编码，可带 UTF-8 BOM。每行写一个选项：

```text
# 分类和餐名之间使用一个 | 分隔
米饭|黄焖鸡米饭
面食|兰州牛肉面

# 不带分类的项目也可以使用
便利店饭团
```

脚本会忽略空行和去除首尾空白后以 `#` 开头的注释行。分类与餐名都会自动去除首尾空白。

每个有效行只能包含至多一个 `|`：

- 没有 `|`：整行是未分类餐名；
- 恰有一个 `|`：格式为 `分类|餐名`；
- 空分类、空餐名或多个 `|`：脚本报错并指出文件路径和行号。

相同的“分类 + 餐名”只保留首次出现的一项；同名但分类不同的项目会保留。

## 筛选与数量

不传 `--category` 时，所有分类和未分类餐食都可被抽取。指定分类后，未分类餐食不会参与抽取。

分类不存在时，脚本会列出可用分类，顺序与菜单中各分类首次出现的顺序一致。`--count` 超过筛选后的可选餐食数时，脚本不会重复推荐，而会报错。

## JSON 输出

```bash
python3 scripts/dinner/random_dinner.py --category 面食 --count 2 --json
```

输出结构如下：

```json
{
  "category": "面食",
  "recommendations": [
    {"name": "兰州牛肉面", "category": "面食"},
    {"name": "重庆小面", "category": "面食"}
  ]
}
```

未指定 `--category` 时，顶层 `category` 为 `null`；未分类餐食的 `category` 也为 `null`。JSON 模式只向标准输出写入 JSON。

## 退出码

- `0`：成功生成推荐。
- `2`：参数、菜单文件、菜单格式、分类或推荐数量有误。错误信息写入标准错误流。

## 限制

内置菜单是通用示例，不会考虑所在地、预算、过敏原、饮食禁忌、营业状态或外卖可得性。建议使用 `--menu-file` 维护符合个人口味和实际可选范围的菜单。

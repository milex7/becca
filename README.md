# Becca 脚本仓库

集中维护可直接运行、依赖尽量少的日常工具脚本。

## 东八区农历日期

`scripts/calendar/chinese_lunar_date.py` 查询东八区当前日期、农历日期、下一个农历正月初一及其前的工作日数。仅需 Python 标准库。

```bash
python3 scripts/calendar/chinese_lunar_date.py
```

指定日期、数据来源、工作日规则与输出说明见 [农历日期查询说明](docs/calendar.md)。

## 随机晚餐推荐

`scripts/dinner/random_dinner.py` 从内置或自定义菜单中随机推荐晚餐。仅需 Python 标准库。

```bash
python3 scripts/dinner/random_dinner.py
```

菜单格式、筛选、JSON 输出与退出码见 [随机晚餐推荐说明](docs/random_dinner.md)。

## 公网出口 IP 与地区查询

`scripts/network/ip_location.py` 对比直连与 HTTP 代理的公网出口 IP 及其地区。仅需 Python 3.10 或更高版本的标准库。

```bash
python3 scripts/network/ip_location.py --proxy http://127.0.0.1:7890
```

代理配置、JSON 输出、退出码和数据来源见 [公网出口 IP 查询说明](docs/ip_location.md)。

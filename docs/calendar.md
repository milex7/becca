# 东八区农历日期查询

`scripts/calendar/chinese_lunar_date.py` 使用 Python 标准库查询东八区（`Asia/Shanghai`）的公历、农历、今年剩余天数、下一个农历正月初一及其前的工作日数。

## 运行

查询当前东八区日期：

```bash
python3 scripts/calendar/chinese_lunar_date.py
```

传入 `YYYY-MM-DD` 复算指定日期：

```bash
python3 scripts/calendar/chinese_lunar_date.py 2026-08-05
```

农历换算覆盖 1900–2099 农历年；查询日期须使下一次正月初一仍落在内置范围内。“今年剩余”不计当天，并以连续自然日换算为完整周和余天；工作日统计不计查询当天、计入正月初一当天。

## 工作日规则

脚本按年份优先读取 [holiday-cn](https://github.com/NateScarlet/holiday-cn) 在线公开的国务院公告 JSON；网络、格式或公告覆盖不可用时，回退到 `data/holiday-cn/` 中的内置副本。

- `isOffDay: true` 表示休息日。
- `isOffDay: false` 表示工作日，包括周末调休。
- 没有可用公告数据的年份，按周一至周五工作、周末休息估算，并在输出中给出估算工作日数量。

内置节假日数据保留 `holiday-cn` 的 MIT 许可。

## 示例

```text
当前日期：2026-08-05（星期三，农历丙午年六月廿三）
今年剩余：148 天（21 周 1 天）
下一个农历正月初一：2027-02-06，相距 185 天
距离正月初一工作日：128 天
估算工作日：26 天
```

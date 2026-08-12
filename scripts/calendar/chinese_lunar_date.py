#!/usr/bin/env python3
"""Print the China Standard Time date alongside its Chinese lunar date.

Only the Python standard library is required.  The bundled lunar-year data
covers 1900–2099, so normal use does not require an annual script update.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


SHANGHAI = ZoneInfo("Asia/Shanghai")
FIRST_LUNAR_YEAR = 1900
LUNAR_EPOCH = date(1900, 1, 31)  # 1900 庚子年正月初一
MONTH_NAMES = ("正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "腊月")
WEEKDAY_NAMES = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")
HEAVENLY_STEMS = "甲乙丙丁戊己庚辛壬癸"
EARTHLY_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
HOLIDAY_DATA_URL = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json"
HOLIDAY_DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "holiday-cn"
HOLIDAY_REQUEST_TIMEOUT_SECONDS = 10

# Each value records the 12 regular months and optional leap month for one
# lunar year. Bits 4–15 describe regular-month lengths (29/30 days), bits
# 0–3 select the leap month, and bit 16 describes its length.
LUNAR_YEAR_INFOS = (
    0x04BD8, 0x04AE0, 0x0A570, 0x054D5, 0x0D260, 0x0D950, 0x16554, 0x056A0, 0x09AD0, 0x055D2,
    0x04AE0, 0x0A5B6, 0x0A4D0, 0x0D250, 0x1D255, 0x0B540, 0x0D6A0, 0x0ADA2, 0x095B0, 0x14977,
    0x04970, 0x0A4B0, 0x0B4B5, 0x06A50, 0x06D40, 0x1AB54, 0x02B60, 0x09570, 0x052F2, 0x04970,
    0x06566, 0x0D4A0, 0x0EA50, 0x06E95, 0x05AD0, 0x02B60, 0x186E3, 0x092E0, 0x1C8D7, 0x0C950,
    0x0D4A0, 0x1D8A6, 0x0B550, 0x056A0, 0x1A5B4, 0x025D0, 0x092D0, 0x0D2B2, 0x0A950, 0x0B557,
    0x06CA0, 0x0B550, 0x15355, 0x04DA0, 0x0A5D0, 0x14573, 0x052B0, 0x0A9A8, 0x0E950, 0x06AA0,
    0x0AEA6, 0x0AB50, 0x04B60, 0x0AAE4, 0x0A570, 0x05260, 0x0F263, 0x0D950, 0x05B57, 0x056A0,
    0x096D0, 0x04DD5, 0x04AD0, 0x0A4D0, 0x0D4D4, 0x0D250, 0x0D558, 0x0B540, 0x0B5A0, 0x195A6,
    0x095B0, 0x049B0, 0x0A974, 0x0A4B0, 0x0B27A, 0x06A50, 0x06D40, 0x0AF46, 0x0AB60, 0x09570,
    0x04AF5, 0x04970, 0x064B0, 0x074A3, 0x0EA50, 0x06B58, 0x05AC0, 0x0AB60, 0x096D5, 0x092E0,
    0x0C960, 0x0D954, 0x0D4A0, 0x0DA50, 0x07552, 0x056A0, 0x0ABB7, 0x025D0, 0x092D0, 0x0CAB5,
    0x0A950, 0x0B4A0, 0x0BAA4, 0x0AD50, 0x055D9, 0x04BA0, 0x0A5B0, 0x15176, 0x052B0, 0x0A930,
    0x07954, 0x06AA0, 0x0AD50, 0x05B52, 0x04B60, 0x0A6E6, 0x0A4E0, 0x0D260, 0x0EA65, 0x0D530,
    0x05AA0, 0x076A3, 0x096D0, 0x04AFB, 0x04AD0, 0x0A4D0, 0x1D0B6, 0x0D250, 0x0D520, 0x0DD45,
    0x0B5A0, 0x056D0, 0x055B2, 0x049B0, 0x0A577, 0x0A4B0, 0x0AA50, 0x1B255, 0x06D20, 0x0ADA0,
    0x14B63, 0x09370, 0x049F8, 0x04970, 0x064B0, 0x168A6, 0x0EA50, 0x06AA0, 0x1A6C4, 0x0AAE0,
    0x092E0, 0x0D2E3, 0x0C960, 0x0D557, 0x0D4A0, 0x0DA50, 0x05D55, 0x056A0, 0x0A6D0, 0x055D4,
    0x052D0, 0x0A9B8, 0x0A950, 0x0B4A0, 0x0B6A6, 0x0AD50, 0x055A0, 0x0ABA4, 0x0A5B0, 0x052B0,
    0x0B273, 0x06930, 0x07337, 0x06AA0, 0x0AD50, 0x14B55, 0x04B60, 0x0A570, 0x054E4, 0x0D160,
    0x0E968, 0x0D520, 0x0DAA0, 0x16AA6, 0x056D0, 0x04AE0, 0x0A9D4, 0x0A2D0, 0x0D150, 0x0F252,
)
LAST_LUNAR_YEAR = FIRST_LUNAR_YEAR + len(LUNAR_YEAR_INFOS) - 1


def lunar_months(year_info: int) -> tuple[tuple[int, int, bool], ...]:
    """Return (month, days, is_leap_month) entries for a lunar year."""
    leap_month = year_info & 0xF
    months: list[tuple[int, int, bool]] = []
    for month in range(1, 13):
        months.append((month, 29 + ((year_info >> (16 - month)) & 1), False))
        if leap_month == month:
            months.append((month, 29 + ((year_info >> 16) & 1), True))
    return tuple(months)


LUNAR_YEAR_DAYS = tuple(sum(days for _, days, _ in lunar_months(info)) for info in LUNAR_YEAR_INFOS)


class HolidayDataError(ValueError):
    """Raised when a holiday-cn year file cannot be used as official data."""


class HolidayYear:
    """Official exceptions for one Gregorian year, or an estimated fallback."""

    def __init__(self, overrides: Mapping[date, bool], source: str) -> None:
        self.overrides = dict(overrides)
        self.source = source


HolidayYearLoader = Callable[[int], HolidayYear]


def holiday_overrides(payload: object, year: int) -> dict[date, bool]:
    """Validate a holiday-cn payload and return date-to-isOffDay overrides."""
    if not isinstance(payload, dict) or payload.get("year") != year:
        raise HolidayDataError("节假日数据年份不匹配")
    papers = payload.get("papers")
    days = payload.get("days")
    if not isinstance(papers, list) or not papers:
        raise HolidayDataError("节假日数据尚无官方公告")
    if not isinstance(days, list):
        raise HolidayDataError("节假日数据缺少日期列表")

    overrides: dict[date, bool] = {}
    for entry in days:
        if not isinstance(entry, dict):
            raise HolidayDataError("节假日日期条目无效")
        value = entry.get("date")
        is_off_day = entry.get("isOffDay")
        if not isinstance(value, str) or not isinstance(is_off_day, bool):
            raise HolidayDataError("节假日日期条目无效")
        try:
            holiday = date.fromisoformat(value)
        except ValueError as error:
            raise HolidayDataError("节假日日期格式无效") from error
        if holiday.year != year:
            raise HolidayDataError("节假日日期不属于指定年份")
        overrides[holiday] = is_off_day
    return overrides


def fetch_holiday_payload(year: int) -> object:
    """Fetch one year's holiday-cn JSON without relying on proxy settings."""
    request = Request(
        HOLIDAY_DATA_URL.format(year=year),
        headers={"Accept": "application/json", "User-Agent": "becca-calendar/1.0"},
    )
    try:
        with urlopen(request, timeout=HOLIDAY_REQUEST_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except (HTTPError, URLError, OSError, TimeoutError, json.JSONDecodeError) as error:
        raise HolidayDataError("无法获取在线节假日数据") from error


def load_local_holiday_payload(year: int, data_directory: Path = HOLIDAY_DATA_DIRECTORY) -> object:
    """Read a vendored holiday-cn JSON file."""
    try:
        with (data_directory / f"{year}.json").open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise HolidayDataError("无法读取本地节假日数据") from error


def load_holiday_year(
    year: int,
    remote_fetcher: Callable[[int], object] = fetch_holiday_payload,
    data_directory: Path = HOLIDAY_DATA_DIRECTORY,
) -> HolidayYear:
    """Prefer online holiday data, then vendored data, then estimate the year."""
    for loader in (
        lambda: remote_fetcher(year),
        lambda: load_local_holiday_payload(year, data_directory),
    ):
        try:
            return HolidayYear(holiday_overrides(loader(), year), "official")
        except HolidayDataError:
            continue
    return HolidayYear({}, "estimated")


def workday_summary(
    start: date,
    end: date,
    holiday_year_loader: HolidayYearLoader = load_holiday_year,
) -> tuple[int, int]:
    """Count workdays inclusively and count those calculated without JSON data."""
    year_data = {
        year: holiday_year_loader(year)
        for year in range(start.year, end.year + 1)
    }
    workday_count = 0
    estimated_workday_count = 0
    current = start
    while current <= end:
        holiday_year = year_data[current.year]
        is_workday = not holiday_year.overrides[current] if current in holiday_year.overrides else current.weekday() < 5
        if is_workday:
            workday_count += 1
            if holiday_year.source == "estimated":
                estimated_workday_count += 1
        current += timedelta(days=1)
    return workday_count, estimated_workday_count


def shanghai_today(now: datetime | None = None) -> date:
    """Return today's Gregorian date in China Standard Time."""
    if now is None:
        now = datetime.now(SHANGHAI)
    return now.astimezone(SHANGHAI).date()


def parse_date(value: str) -> date:
    """Parse a strict ISO calendar date."""
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("日期必须使用有效的 YYYY-MM-DD 格式") from error


def sexagenary_year(year: int) -> str:
    return f"{HEAVENLY_STEMS[(year - 4) % 10]}{EARTHLY_BRANCHES[(year - 4) % 12]}"


def chinese_day(day: int) -> str:
    if not 1 <= day <= 30:
        raise ValueError("农历日期超出范围")
    digits = "一二三四五六七八九十"
    if day <= 10:
        return f"初{digits[day - 1]}"
    if day < 20:
        return f"十{digits[day - 11]}"
    if day == 20:
        return "二十"
    if day < 30:
        return f"廿{digits[day - 21]}"
    return "三十"


def lunar_components(value: date) -> tuple[int, int, int, bool]:
    """Convert a supported Gregorian date to lunar year, month, day and leap flag."""
    offset = (value - LUNAR_EPOCH).days
    if offset < 0:
        raise ValueError(f"内置农历数据仅覆盖 {LUNAR_EPOCH.isoformat()} 起的日期")

    for index, year_days in enumerate(LUNAR_YEAR_DAYS):
        if offset < year_days:
            lunar_year = FIRST_LUNAR_YEAR + index
            for month, month_days, is_leap_month in lunar_months(LUNAR_YEAR_INFOS[index]):
                if offset < month_days:
                    return lunar_year, month, offset + 1, is_leap_month
                offset -= month_days
        else:
            offset -= year_days
    raise ValueError(f"内置农历数据仅覆盖至 {LAST_LUNAR_YEAR} 农历年")


def lunar_new_year(lunar_year: int) -> date:
    """Return the Gregorian date of a supported lunar year's first day."""
    if not FIRST_LUNAR_YEAR <= lunar_year <= LAST_LUNAR_YEAR:
        raise ValueError(f"内置农历数据仅覆盖 {FIRST_LUNAR_YEAR}–{LAST_LUNAR_YEAR} 农历年")
    offset = sum(LUNAR_YEAR_DAYS[: lunar_year - FIRST_LUNAR_YEAR])
    return LUNAR_EPOCH + timedelta(days=offset)


def lunar_date(value: date) -> str:
    lunar_year, month, day, is_leap_month = lunar_components(value)
    leap_prefix = "闰" if is_leap_month else ""
    return f"{sexagenary_year(lunar_year)}年{leap_prefix}{MONTH_NAMES[month - 1]}{chinese_day(day)}"


def calendar_summary(
    value: date,
    holiday_year_loader: HolidayYearLoader = load_holiday_year,
) -> dict[str, str | int]:
    lunar_year, _, _, _ = lunar_components(value)
    if lunar_year == LAST_LUNAR_YEAR:
        raise ValueError("无法查询该数据范围内最后一个农历年的下一次正月初一")

    next_new_year = lunar_new_year(lunar_year + 1)
    remaining_days = (date(value.year + 1, 1, 1) - value).days - 1
    remaining_weeks, remaining_week_days = divmod(remaining_days, 7)
    workday_count, estimated_workday_count = workday_summary(
        value + timedelta(days=1), next_new_year, holiday_year_loader
    )
    return {
        "date": value.isoformat(),
        "weekday": WEEKDAY_NAMES[value.weekday()],
        "lunar_date": lunar_date(value),
        "remaining_days": remaining_days,
        "remaining_weeks": remaining_weeks,
        "remaining_week_days": remaining_week_days,
        "next_lunar_new_year": next_new_year.isoformat(),
        "days_to_lunar_new_year": (next_new_year - value).days,
        "workday_count": workday_count,
        "estimated_workday_count": estimated_workday_count,
    }


def format_summary(summary: dict[str, str | int]) -> str:
    lines = [
            f"当前日期：{summary['date']}（{summary['weekday']}，农历{summary['lunar_date']}）",
            "今年剩余："
            f"{summary['remaining_days']} 天（{summary['remaining_weeks']} 周 {summary['remaining_week_days']} 天）",
            "下一个农历正月初一："
            f"{summary['next_lunar_new_year']}，相距 {summary['days_to_lunar_new_year']} 天",
            f"距离正月初一工作日：{summary['workday_count']} 天",
    ]
    estimated_workday_count = summary["estimated_workday_count"]
    assert isinstance(estimated_workday_count, int)
    if estimated_workday_count:
        lines.append(f"估算工作日：{estimated_workday_count} 天")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="查询东八区当前日期和中国农历日期")
    parser.add_argument("date", nargs="?", type=parse_date, help="要复算的日期（YYYY-MM-DD）")
    arguments = parser.parse_args()
    try:
        print(format_summary(calendar_summary(arguments.date or shanghai_today())))
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Show direct and HTTP-proxy public egress IP location observations."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import ipaddress
import json
import os
import socket
import sys
from typing import Any, Callable, Iterator, Mapping, Sequence
import urllib.error
import urllib.parse
import urllib.request


IPWHO_BASE_URL = "https://ipwho.is"
IPWHO_QUERY = "lang=zh-CN&fields=success,message,ip,country,region,city"
IPIFY_URL = "https://api.ipify.org?format=json"
REQUEST_TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 64 * 1024
DEFAULT_PROXY_URL = "http://127.0.0.1:7890"
PROXY_ENV_VARS = (
    "HTTPS_PROXY",
    "https_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "ALL_PROXY",
    "all_proxy",
)

Observation = dict[str, Any]
Lookup = Callable[[], Observation]
ProxyLookup = Callable[[str], Observation]


def success_observation(
    ip: str,
    country: str | None,
    region: str | None,
    city: str | None,
) -> Observation:
    return {
        "status": "ok",
        "ip": ip,
        "country": country,
        "region": region,
        "city": city,
    }


def error_observation(code: str, message: str) -> Observation:
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
        },
    }


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _fetch_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    service_name: str,
) -> tuple[dict[str, Any] | None, Observation | None]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "becca-ip-location/1.0",
        },
    )

    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        return None, error_observation(
            "http_error", f"{service_name}返回 HTTP {exc.code}"
        )
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            return None, error_observation("timeout", f"{service_name}请求超时")
        return None, error_observation("network_error", f"无法连接{service_name}")
    except (TimeoutError, socket.timeout):
        return None, error_observation("timeout", f"{service_name}请求超时")
    except OSError:
        return None, error_observation("network_error", f"无法连接{service_name}")

    if len(raw) > MAX_RESPONSE_BYTES:
        return None, error_observation(
            "invalid_response", f"{service_name}响应过大"
        )

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, error_observation(
            "invalid_response", f"{service_name}返回了无法解析的数据"
        )

    if not isinstance(payload, dict):
        return None, error_observation(
            "invalid_response", f"{service_name}返回了无效的数据结构"
        )
    return payload, None


def _valid_ip(payload: Mapping[str, Any], service_name: str) -> tuple[str | None, Observation | None]:
    ip = payload.get("ip")
    if not isinstance(ip, str):
        return None, error_observation(
            "invalid_response", f"{service_name}响应缺少有效的公网 IP"
        )

    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return None, error_observation(
            "invalid_response", f"{service_name}响应缺少有效的公网 IP"
        )
    return ip, None


def _query_location(
    opener: urllib.request.OpenerDirector,
    ip: str | None = None,
) -> Observation:
    endpoint = (
        f"{IPWHO_BASE_URL}/"
        if ip is None
        else f"{IPWHO_BASE_URL}/{urllib.parse.quote(ip, safe=':')}"
    )
    payload, error = _fetch_json(
        opener,
        f"{endpoint}?{IPWHO_QUERY}",
        "地区查询服务",
    )
    if error is not None:
        return error
    assert payload is not None

    if payload.get("success") is False:
        message = _optional_text(payload.get("message")) or "地区查询服务拒绝了请求"
        return error_observation("service_error", message)

    if payload.get("success") is not True:
        return error_observation("invalid_response", "地区查询服务响应缺少成功标识")

    observed_ip, ip_error = _valid_ip(payload, "地区查询服务")
    if ip_error is not None:
        return ip_error
    assert observed_ip is not None

    return success_observation(
        ip=observed_ip,
        country=_optional_text(payload.get("country")),
        region=_optional_text(payload.get("region")),
        city=_optional_text(payload.get("city")),
    )


def _query_public_ip(
    opener: urllib.request.OpenerDirector,
) -> tuple[str | None, Observation | None]:
    payload, error = _fetch_json(
        opener,
        IPIFY_URL,
        "代理出口 IP 服务",
    )
    if error is not None:
        return None, error
    assert payload is not None
    return _valid_ip(payload, "代理出口 IP 服务")


def lookup_direct() -> Observation:
    """Query through an opener that never consults proxy environment variables."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return _query_location(opener)


@contextmanager
def _ignore_proxy_bypass() -> Iterator[None]:
    """Prevent NO_PROXY and platform proxy settings from bypassing our proxy."""
    saved = {
        key: value
        for key, value in os.environ.items()
        if key.casefold() == "no_proxy"
    }
    for key in list(os.environ):
        if key.casefold() == "no_proxy":
            del os.environ[key]

    # A non-empty no_proxy value makes urllib use environment bypass rules on
    # platforms such as macOS, while this sentinel cannot match the API host.
    os.environ["no_proxy"] = "__becca_force_http_proxy__"
    try:
        yield
    finally:
        for key in list(os.environ):
            if key.casefold() == "no_proxy":
                del os.environ[key]
        os.environ.update(saved)


def lookup_proxy(proxy_url: str) -> Observation:
    """Observe the proxy IP, then geolocate that IP over a direct connection."""
    proxy_opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"https": proxy_url})
    )
    with _ignore_proxy_bypass():
        proxy_ip, error = _query_public_ip(proxy_opener)
    if error is not None:
        return error
    assert proxy_ip is not None

    direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return _query_location(direct_opener, proxy_ip)


def select_proxy(
    argument: str | None,
    environ: Mapping[str, str],
) -> tuple[str, str]:
    if argument is not None:
        return argument, "argument"

    for name in PROXY_ENV_VARS:
        value = environ.get(name)
        if value:
            return value, name
    return DEFAULT_PROXY_URL, "default"


def validate_proxy(proxy_url: str) -> str | None:
    """Return a safe validation message, never the supplied proxy URL."""
    if not proxy_url or any(character.isspace() for character in proxy_url):
        return "代理地址格式无效"

    try:
        parsed = urllib.parse.urlsplit(proxy_url)
        port = parsed.port
    except ValueError:
        return "代理地址格式无效"

    if parsed.scheme.lower() != "http":
        return "仅支持 http:// 代理"
    if parsed.username is not None or parsed.password is not None:
        return "首版不支持需要认证的代理"
    if not parsed.hostname or port is None or port == 0:
        return "代理地址必须包含主机名和端口"
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        return "代理地址不能包含路径、查询参数或片段"
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="查询直连与 HTTP 代理的公网出口 IP 和地区",
    )
    parser.add_argument(
        "--proxy",
        metavar="HTTP_URL",
        help=f"HTTP 代理地址（默认：{DEFAULT_PROXY_URL}）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出",
    )
    return parser


def _render_observation(label: str, observation: Observation) -> list[str]:
    lines = [label]
    if observation["status"] == "ok":
        location = " / ".join(
            observation[field] or "-" for field in ("country", "region", "city")
        )
        lines.extend(
            (
                "  状态: 成功",
                f"  IP: {observation['ip']}",
                f"  地区: {location}",
            )
        )
    else:
        lines.extend(
            (
                "  状态: 失败",
                f"  错误: {observation['error']['message']}",
            )
        )
    return lines


def render_text(result: dict[str, Any]) -> str:
    lines = _render_observation("直连出口", result["direct"])
    lines.append("")
    lines.extend(_render_observation("代理出口", result["proxy"]))

    source = result["proxy_source"]
    if source:
        display_source = "--proxy" if source == "argument" else source
        lines.append(f"  来源: {display_source}")

    if result["warnings"]:
        lines.append("")
        lines.extend(f"警告: {warning}" for warning in result["warnings"])
    return "\n".join(lines)


def run(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    direct_lookup: Lookup | None = None,
    proxy_lookup: ProxyLookup | None = None,
) -> int:
    args = _build_parser().parse_args(argv)
    environment = os.environ if environ is None else environ
    direct_query = lookup_direct if direct_lookup is None else direct_lookup
    proxy_query = lookup_proxy if proxy_lookup is None else proxy_lookup

    proxy_url, proxy_source = select_proxy(args.proxy, environment)
    configuration_error = validate_proxy(proxy_url)

    direct = direct_query()
    if configuration_error is not None:
        proxy = error_observation("invalid_proxy", configuration_error)
    else:
        proxy = proxy_query(proxy_url)

    warnings: list[str] = []
    if (
        direct["status"] == "ok"
        and proxy["status"] == "ok"
        and direct["ip"] == proxy["ip"]
    ):
        warnings.append("代理未改变公网出口")

    result = {
        "direct": direct,
        "proxy": proxy,
        "proxy_source": proxy_source,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))

    if configuration_error is not None:
        return 2
    if direct["status"] != "ok" or proxy["status"] != "ok":
        return 1
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()

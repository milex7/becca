# Becca 脚本仓库

集中维护可直接运行、依赖尽量少的日常工具脚本。

## 东八区农历日期

`scripts/calendar/chinese_lunar_date.py` 仅使用 Python 标准库，输出东八区（`Asia/Shanghai`）当前日期、农历日期、今年剩余天数、下一个农历正月初一的日期与距离，以及该日期前的工作日数。脚本内置 1900–2099 农历年数据；无需安装第三方依赖，也不需要 Node.js。

```bash
python3 scripts/calendar/chinese_lunar_date.py
```

可传入 `YYYY-MM-DD` 复算指定日期；“今年剩余”不包含当天，距离按日期差计算。可查询 1900-01-31 起至 2099 农历年范围内、且下一次正月初一仍在内置数据范围的日期：

```bash
python3 scripts/calendar/chinese_lunar_date.py 2026-08-05
```

输出：

```text
当前日期：2026-08-05（星期三，农历丙午年六月廿三）
今年剩余：148 天
下一个农历正月初一：2027-02-06，相距 185 天
距离正月初一工作日：128 天
估算工作日：26 天
```

工作日优先采用 [holiday-cn](https://github.com/NateScarlet/holiday-cn) 在线公开的当年国务院公告数据；网络、数据格式或公告覆盖不可用时，脚本回退到内置副本。两者均不可用时，按周一至周五工作、周末休息估算，并在输出中标注估算工作日数量。内置数据位于 `data/holiday-cn/`，并保留其 MIT 许可。

## 公网出口 IP 与地区查询

`scripts/network/ip_location.py` 分别查询：

- **直连出口**：强制绕过系统和环境代理后，公网服务观察到的 IP。
- **代理出口**：强制通过指定 HTTP 代理获取公网 IP，再通过直连查询该 IP 的地区。

每条结果包含实际使用的 IPv4 或 IPv6，以及中文国家、省州和城市。脚本要求 Python 3.10 或更高版本，仅使用 Python 标准库。

### 运行

macOS 或 Linux：

```bash
python3 scripts/network/ip_location.py --proxy http://127.0.0.1:7890
```

脚本具有 Unix 可执行权限，也可以直接运行：

```bash
./scripts/network/ip_location.py --proxy http://127.0.0.1:7890
```

Windows PowerShell：

```powershell
py -3 scripts/network/ip_location.py --proxy http://127.0.0.1:7890
```

如未传入 `--proxy`，脚本按以下顺序读取环境变量：

```text
HTTPS_PROXY, https_proxy, HTTP_PROXY, http_proxy, ALL_PROXY, all_proxy
```

如果这些环境变量也都没有设置，脚本默认使用本机 HTTP 代理 `http://127.0.0.1:7890`。完整优先级为：命令行参数、代理环境变量、本机 7890 默认端口。

macOS/Linux 环境变量示例：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
python3 scripts/network/ip_location.py
```

Windows PowerShell 环境变量示例：

```powershell
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
py -3 scripts/network/ip_location.py
```

首版只支持无需认证且包含端口的 `http://` 代理，不支持 SOCKS、HTTPS 代理、代理账号密码或操作系统 GUI 代理自动发现。

### JSON 输出

使用 `--json` 获得稳定的机器可读结果：

```bash
python3 scripts/network/ip_location.py \
  --proxy http://127.0.0.1:7890 \
  --json
```

```json
{
  "direct": {
    "status": "ok",
    "ip": "203.0.113.10",
    "country": "中国",
    "region": "上海市",
    "city": "上海市"
  },
  "proxy": {
    "status": "ok",
    "ip": "198.51.100.20",
    "country": "日本",
    "region": "东京都",
    "city": "东京"
  },
  "proxy_source": "argument",
  "warnings": []
}
```

失败的出口使用 `{"status": "error", "error": {"code": "...", "message": "..."}}`。地区数据缺失时，对应 JSON 字段为 `null`；默认文本输出显示为 `-`。输出不会包含代理 URL。

### 退出码

- `0`：直连和代理查询都成功；两者 IP 相同时仍成功，但会显示警告。
- `1`：网络、超时、HTTP 或查询服务错误导致结果不完整。
- `2`：显式参数或环境变量中的代理配置非法。

两条查询互相独立；其中一条失败时，另一条成功结果仍会输出。每次网络请求的超时时间为 10 秒。

### 数据来源与限制

直连 IP 和地区查询来自 [ipwho.is](https://ipwhois.io/documentation)，代理出口 IP 来自 [ipify](https://www.ipify.org/)，所有请求均使用 HTTPS 且不需要 API 密钥。代理出口的地区通过直连查询其 IP 获得，避免定位服务与部分代理线路不兼容。ipwho.is 免费服务当前限制为每天 1,000 次请求；一次完整运行会调用两次 ipwho.is 和一次 ipify。IP 地理位置是近似信息，不应视为精确地址。

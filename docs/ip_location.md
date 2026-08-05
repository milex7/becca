# 公网出口 IP 与地区查询

`scripts/network/ip_location.py` 分别查询直连出口和 HTTP 代理出口的公网 IP 及其近似地区。

- **直连出口**：显式绕过系统和环境代理后的公网出口。
- **代理出口**：通过选定 HTTP 代理取得公网 IP，再通过直连查询该 IP 的地区。

每条结果包含 IPv4 或 IPv6、中文国家、省州和城市。

## 运行与代理配置

macOS 或 Linux：

```bash
python3 scripts/network/ip_location.py --proxy http://127.0.0.1:7890
```

Windows PowerShell：

```powershell
py -3 scripts/network/ip_location.py --proxy http://127.0.0.1:7890
```

未传入 `--proxy` 时，脚本依次读取 `HTTPS_PROXY`、`https_proxy`、`HTTP_PROXY`、`http_proxy`、`ALL_PROXY`、`all_proxy`；都不存在时默认使用 `http://127.0.0.1:7890`。优先级为命令行参数、代理环境变量、本机默认端口。

仅支持无需认证、包含端口的 `http://` 代理；不支持 SOCKS、HTTPS 代理、代理账号密码或操作系统 GUI 代理自动发现。

## JSON 输出

使用 `--json` 获取稳定的机器可读结果：

```bash
python3 scripts/network/ip_location.py --proxy http://127.0.0.1:7890 --json
```

每个出口成功时包含 `status`、`ip`、`country`、`region`、`city`；失败时包含 `status: "error"` 和错误代码、消息。地区缺失时 JSON 字段为 `null`，文本输出显示 `-`。输出不会包含代理 URL。

## 退出码与数据来源

- `0`：直连和代理查询均成功；两者 IP 相同仍成功，但会显示警告。
- `1`：网络、超时、HTTP 或服务错误导致结果不完整。
- `2`：显式参数或环境变量中的代理配置无效。

两条查询互相独立，单条失败不会抑制另一条结果；单次网络请求超时为 10 秒。

直连 IP 和地区使用 [ipwho.is](https://ipwhois.io/documentation)，代理出口 IP 使用 [ipify](https://www.ipify.org/)。所有请求均为 HTTPS 且无需 API 密钥。ipwho.is 免费服务限制为每天 1,000 次；一次完整查询调用两次 ipwho.is 和一次 ipify。IP 地理位置为近似信息，不应视作精确地址。

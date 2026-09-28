# 随机密码生成

`scripts/security/password_generator.py` 使用 Python 标准库生成由数字及大小写英文字母组成的随机密码。随机选择由 `secrets` 提供，适用于密码等安全敏感用途。

## 运行

默认生成 12 位密码：

```bash
python3 scripts/security/password_generator.py
```

使用 `--length` 或 `-l` 指定长度：

```bash
python3 scripts/security/password_generator.py --length 24
python3 scripts/security/password_generator.py -l 16
```

长度必须是大于 0 的整数。命令只向标准输出打印生成的密码；参数无效时显示错误并以非零状态退出。

## 字符范围与限制

字符集包含 `A-Z`、`a-z` 和 `0-9`。每一位都从完整字符集中独立随机选取，因此不会保证结果一定包含数字、大写字母和小写字母各至少一个。脚本不访问网络，也不保存生成的密码。

#!/bin/bash
umask 077
ROOT="$(cd "$(dirname "$0")" && pwd)"
/usr/bin/python3 "$ROOT/macos/tools/collect-hang.py"
read -r -p '按回车关闭诊断窗口。'

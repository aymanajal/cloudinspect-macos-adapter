#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo '正在启动云巡检 Mac 版。运行数据保存在 macos/app。'
"$ROOT/macos/run-mac.sh"
status=$?
if [ "$status" -ne 0 ]; then
  echo "启动退出（状态 $status）。请检查 macos/app/logs/macos-launch.log。"
  read -r -p '按回车关闭窗口。'
fi
exit "$status"

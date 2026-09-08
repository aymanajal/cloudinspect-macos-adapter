#!/usr/bin/env python3
"""Read-only hang capture: never signals, restarts, or attaches a debugger."""
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
root = Path(__file__).resolve().parents[1]
jdk = root / 'runtime/zulu8.96.0.205-ca-fx-jdk8.0.504-macosx_aarch64/Contents/Home'
rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,command='], text=True)
pids = []
for row in rows.splitlines():
    parts = row.strip().split(None, 1)
    if len(parts) == 2 and parts[1].startswith(str(jdk / 'bin/java') + ' ') and ' cloudinspect.macos.Launcher' in parts[1]:
        pids.append(int(parts[0]))
if not pids:
    print('未发现当前目录启动的云巡检进程。请在卡住时运行此工具。')
    sys.exit(2)
out = root / 'diagnostics' / ('hang-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
out.mkdir(mode=0o700)
for pid in pids:
    for index in range(2):
        try:
            result = subprocess.run([str(jdk / 'bin/jstack'), '-l', str(pid)], capture_output=True, timeout=12)
            (out / ('threads-%s-%s.txt' % (pid, index))).write_bytes(result.stdout + result.stderr)
        except subprocess.TimeoutExpired as exc:
            (out / ('threads-%s-%s.txt' % (pid, index))).write_bytes((exc.stdout or b'') + (exc.stderr or b'') + b'\nThread capture timed out; application untouched.\n')
        if index == 0:
            time.sleep(2)
    status = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'pid,ppid,stat,%cpu,%mem,etime'], capture_output=True)
    (out / ('process-%s.txt' % pid)).write_bytes(status.stdout + status.stderr)
for name in ('macos-launch.log', 'cloudinspect-error.log', 'cloudinspect-log.log'):
    log = root / 'app/logs' / name
    if log.exists():
        with log.open('rb') as stream:
            stream.seek(max(0, log.stat().st_size - 128 * 1024))
            (out / name).write_bytes(stream.read())
print('诊断已保存到：' + str(out))
print('没有关闭或重启程序。诊断文件仅保存在本机，可能包含日志中的业务信息。')

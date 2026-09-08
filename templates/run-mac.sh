#!/bin/bash
set -euo pipefail
umask 077
MAC_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$MAC_DIR/app"
JAVA_HOME="$MAC_DIR/runtime/zulu8.96.0.205-ca-fx-jdk8.0.504-macosx_aarch64/Contents/Home"
export JAVA_HOME
export PATH="$JAVA_HOME/bin:$PATH"
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo '此版本需要 Apple Silicon Mac。'; exit 1
fi
if [[ ! -x "$JAVA_HOME/bin/java" ]]; then
  echo '缺少 Mac Java 运行环境，请保留完整的 macos 目录。'; exit 1
fi
mkdir -p logs
/usr/bin/shasum -a 256 -c "$MAC_DIR/checksums.sha256" >/dev/null || { echo 'Mac 程序文件已变化，需要重新适配。'; exit 1; }
JAVA_ARGS=(-XX:MetaspaceSize=256m -XX:MaxMetaspaceSize=1024m -Dfile.encoding=UTF-8 -Djava.awt.headless=false)
if [[ "${1:-}" == --smoke ]]; then
  JAVA_ARGS+=(-Dcloudinspect.smoke=true -Dcloudinspect.smoke.patch=true)
  exec /usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' "$JAVA_HOME/bin/java" "${JAVA_ARGS[@]}" -cp "$MAC_DIR/macos-support.jar:CloudInspect-mac.jar:lib/*" cloudinspect.macos.Launcher
fi
exec "$JAVA_HOME/bin/java" "${JAVA_ARGS[@]}" -cp "$MAC_DIR/macos-support.jar:CloudInspect-mac.jar:lib/*" cloudinspect.macos.Launcher >> logs/macos-launch.log 2>&1

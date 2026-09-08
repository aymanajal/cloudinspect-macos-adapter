# CloudInspect macOS 适配工具

将用户自有的用友云巡检工具复制为可在 Apple Silicon Mac 上运行的独立版本。仓库仅包含适配源码、安装脚本及诊断工具，不包含原厂 JAR、Java 二进制、数据库、服务器配置、业务补丁或日志。

这是非官方适配，不代表原厂提供 macOS 支持。已验证主界面及补丁管理界面渲染；服务器连接、补丁安装、备份和回退需在目标测试环境验证。

## 支持范围

- Apple Silicon（M 系列）macOS。Intel Mac 暂不支持。
- Python 3、curl、unzip。首次编译需系统具备可运行的 Python 3；运行生成后的应用不需要 Python（采集诊断除外）。
- Java 8.0.504 ARM64 JDK FX，由安装脚本从 Azul 官方下载并校验 SHA-256。
- 只支持以下已验证原版 `CloudInspect.jar`，脚本遇到其他版本会停止：

```text
6a7b37a840aeb7cda0605cc7d510fbb2b526a63c4f20bfc7bce1105a1ce1e617
```

## 安装

先正常退出原工具，保持数据库处于关闭状态。获取本仓库后执行（替换原版包的实际位置）：

```bash
python3 install.py \
  --source "$HOME/Desktop/CloudInspect" \
  --output "$HOME/Desktop/CloudInspect-Mac"
```

输出目录必须不存在。脚本在临时目录完成编译及校验后才生成最终目录，不覆盖原版工具或已有适配目录，也不会自动启动或联网访问业务服务器。

已有相同版本的 Zulu JDK FX 时可以避免重复下载：

```bash
python3 install.py \
  --source "$HOME/Desktop/CloudInspect" \
  --output "$HOME/Desktop/CloudInspect-Mac-New" \
  --runtime "$HOME/Desktop/CloudInspect/macos/runtime/zulu8.96.0.205-ca-fx-jdk8.0.504-macosx_aarch64"
```

`--runtime` 使用你提供的本地运行环境，只校验版本、架构和 JavaFX 是否存在；不会重新证明其来源或归档哈希。

安装会在本机复制原包的数据库、配置、安装记录、关联补丁、模板和报告，不会上传它们。未复制 Windows Java、工具自身的待升级包及旧升级标记。新副本关闭定时任务，保留原云连接设置。旧记录中的 Windows 绝对路径需在界面重新选择。

## 使用及迁移

双击生成目录内的 `启动云巡检-Mac.command`。若执行权限在传输后丢失：

```bash
chmod +x "$HOME/Desktop/CloudInspect-Mac/启动云巡检-Mac.command"
chmod +x "$HOME/Desktop/CloudInspect-Mac/macos/run-mac.sh"
```

迁移至另一台 M 系列 Mac 时，先退出应用，再完整复制生成目录。Java 已内置，目录可改名、移动，也支持空格和中文路径。**生成目录包含原环境数据，不是本仓库的可公开发布内容。** 给其他使用者分发本仓库，让其使用自己的原版包构建。

正常启动允许联网，可能自动检查原配置服务器及云端。请先核对目标环境。新机器的 VPN、网络路由和服务端权限仍需单独配置。

## 实现

ASM 仅改写三个方法，其他 JAR 条目逐字节核验一致：

| 方法 | 适配行为 |
| --- | --- |
| `Director.openFile` | 通过 `/usr/bin/open` 打开本地文件，参数独立传递 |
| `InterfaceUtils.setTipTime` | 用 JavaFX 公开 API 设置提示显示时间 |
| `VersionUpdate.clientUpdate` | 将客户端自身的一键升级改为提示，防止覆盖适配版 |

业务补丁安装、备份和回退代码未修改。单实例文件锁位于新副本，启动器校验主 JAR 和支持 JAR，避免混用版本。不支持直接安装原工具升级包；更换版本需重新适配。

## 卡顿诊断

不要在补丁安装或未保存时强制退出。卡住时双击 `采集卡死诊断-Mac.command`，采集两份线程堆栈、进程状态及最近日志，不关闭、不重启程序。

文件保存在 `macos/diagnostics/hang-*`，可能含业务信息，仅留在本机，不要直接提交到 GitHub。提示框使用模态窗口，未关闭时主窗口无法点击，不一定是死锁。

## 验证模式

```bash
/path/to/CloudInspect-Mac/macos/run-mac.sh --smoke
```

使用 macOS `sandbox-exec` 禁止网络，启动后采集界面快照并打开补丁管理页面，不触发补丁安装。此模式也可能限制部分系统调用，日志里的沙箱拒绝不等于正常模式存在同样问题。快照、窗口数与空列表不能证明联网业务正常。

构建只对 JAR 修改范围、Java 版本和架构进行验证。实际联网与生产补丁操作不属于已完成验收。

## 原厂组件

使用者自行取得原版工具并遵守其许可。此仓库不再分发原厂代码或业务数据。运行环境来自 [Azul 官方下载站](https://www.azul.com/downloads/?os=macos&package=jdk-fx&version=java-8-lts)，其许可文件保留在运行环境中。

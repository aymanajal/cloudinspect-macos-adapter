#!/usr/bin/env python3
"""Build a private, local CloudInspect macOS copy from a user-owned distribution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import zipfile

ORIGINAL_SHA256 = '6a7b37a840aeb7cda0605cc7d510fbb2b526a63c4f20bfc7bce1105a1ce1e617'
RUNTIME_NAME = 'zulu8.96.0.205-ca-fx-jdk8.0.504-macosx_aarch64'
RUNTIME_URL = 'https://cdn.azul.com/zulu/bin/' + RUNTIME_NAME + '.zip'
RUNTIME_SHA256 = '8efec900203492b1ac3dbeffee374f232862d029c0d03558cdbcfc51057f8cb7'
CHANGED_CLASSES = {
    'nc/cloudinspect/ui/utils/Director.class',
    'nc/cloudinspect/ui/utils/InterfaceUtils.class',
    'nc/cloudinspect/service/update/VersionUpdate.class',
}

def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def copy_tree(source, target):
    # APFS clones avoid duplicating large patch archives. Fall back on other disks.
    result = subprocess.run(['/bin/cp', '-cR', str(source), str(target)], capture_output=True)
    if result.returncode:
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, symlinks=True)

def verify_patch(original, patched):
    with zipfile.ZipFile(original) as before, zipfile.ZipFile(patched) as after:
        if before.namelist() != after.namelist():
            raise RuntimeError('JAR 条目发生非预期变化')
        changed = {n for n in before.namelist() if before.read(n) != after.read(n)}
        if changed != CHANGED_CLASSES:
            raise RuntimeError('JAR 修改范围不符合预期：' + repr(changed))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='自有原版 CloudInspect 目录，安装时请关闭该工具')
    parser.add_argument('--output', required=True, type=Path, help='新的输出目录；不覆盖已存在目录')
    parser.add_argument('--runtime', type=Path, help='可选：已解压的同版 Zulu JDK 根目录（其中有 Contents/Home）')
    args = parser.parse_args()
    source, output = args.source.expanduser().resolve(), args.output.expanduser().absolute()
    repo = Path(__file__).resolve().parent
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        parser.error('当前版本只支持 Apple Silicon macOS；Intel 尚未适配')
    if output.exists() or output.is_symlink():
        parser.error('输出目录已存在；请选择新目录，避免覆盖工作数据')
    required = ['CloudInspect.jar', 'lib/asm-9.8.jar', 'resources/db', 'config', 'resources/template']
    for name in required:
        if not (source / name).exists():
            parser.error('缺少原版文件：' + name)
    if sha256(source / 'CloudInspect.jar') != ORIGINAL_SHA256:
        parser.error('原版 JAR 版本未验证，已停止；不能直接对其他版本套用字节码修改')
    if (source / 'resources/db/cidb.lock.db').exists():
        parser.error('发现原版数据库锁，请先正常关闭原工具，再安装')
    if args.runtime:
        runtime_source = args.runtime.expanduser().resolve()
        if not (runtime_source / 'Contents/Home/bin/javac').is_file():
            parser.error('--runtime 应指向包含 Contents/Home 的 JDK 根目录')
    output.parent.mkdir(parents=True, exist_ok=True)
    os.umask(0o077)
    staging = Path(tempfile.mkdtemp(prefix='.cloudinspect-build-', dir=str(output.parent)))
    try:
        mac = staging / 'macos'
        app = mac / 'app'
        app.mkdir(parents=True)
        (mac / 'runtime').mkdir()
        (mac / 'classes').mkdir()
        (mac / 'diagnostics').mkdir()
        runtime = mac / 'runtime' / RUNTIME_NAME
        if args.runtime:
            print('复制本地 JavaFX 运行环境…', flush=True)
            copy_tree(runtime_source, runtime)
        else:
            print('从 Azul 官方下载 ARM64 Java 8 / JavaFX…', flush=True)
            archive = staging / 'runtime.zip'
            subprocess.run(['curl', '-fL', '--retry', '2', RUNTIME_URL, '-o', str(archive)], check=True)
            if sha256(archive) != RUNTIME_SHA256:
                raise RuntimeError('运行环境 SHA-256 校验失败')
            subprocess.run(['/usr/bin/unzip', '-q', str(archive), '-d', str(mac / 'runtime')], check=True)
            archive.unlink()
        jdk = runtime / 'Contents/Home'
        version = subprocess.run([str(jdk / 'bin/java'), '-XshowSettings:properties', '-version'],
                                 check=True, capture_output=True, text=True).stderr
        if 'java.version = 1.8.0_504' not in version or 'os.arch = aarch64' not in version:
            raise RuntimeError('需要已验证的 Java 8.0.504 aarch64 运行环境')
        if not (jdk / 'jre/lib/ext/jfxrt.jar').is_file():
            raise RuntimeError('缺少 JavaFX')
        print('复制本地配置及关联记录（只留在输出目录，不上传）…', flush=True)
        for name in ['lib', 'config', 'install', 'buding', 'report']:
            if (source / name).is_dir():
                copy_tree(source / name, app / name)
        (app / 'resources').mkdir()
        for name in ['db', 'template', 'initData']:
            if (source / 'resources' / name).is_dir():
                copy_tree(source / 'resources' / name, app / 'resources' / name)
        (app / 'download').mkdir()
        for name in ['patch', 'safePatch']:
            if (source / 'download' / name).is_dir():
                copy_tree(source / 'download' / name, app / 'download' / name)
        # Preserve other settings; disable scheduled jobs in the newly built copy.
        config = app / 'config/config.properties'
        data = config.read_bytes() if config.exists() else b''
        config.write_bytes(data + b'\ntimerEnable=false\n')
        copy_tree(repo / 'src', mac / 'src')
        copy_tree(repo / 'tools', mac / 'tools')
        classpath = str(source / 'CloudInspect.jar') + os.pathsep + str(app / 'lib/*')
        print('编译启动器并适配三个方法…', flush=True)
        subprocess.run([str(jdk / 'bin/javac'), '-cp', classpath, '-d', str(mac / 'classes')]
                       + [str(p) for p in sorted((mac / 'src').glob('*.java'))], check=True)
        patched = app / 'CloudInspect-mac.jar'
        subprocess.run([str(jdk / 'bin/java'), '-cp', str(mac / 'classes') + os.pathsep + str(app / 'lib/asm-9.8.jar'),
                        'BuildPatch', str(source / 'CloudInspect.jar'), str(patched)], check=True)
        verify_patch(source / 'CloudInspect.jar', patched)
        support = mac / 'macos-support.jar'
        subprocess.run([str(jdk / 'bin/jar'), 'cf', str(support), '-C', str(mac / 'classes'), 'cloudinspect'], check=True)
        (mac / 'checksums.sha256').write_text(sha256(patched) + '  CloudInspect-mac.jar\n'
                                             + sha256(support) + '  ../macos-support.jar\n')
        for name in ['启动云巡检-Mac.command', '采集卡死诊断-Mac.command']:
            shutil.copy2(repo / 'templates' / name, staging / name)
            (staging / name).chmod(0o700)
        shutil.copy2(repo / 'templates/run-mac.sh', mac / 'run-mac.sh')
        (mac / 'run-mac.sh').chmod(0o700)
        shutil.copy2(repo / 'README.md', staging / 'Mac使用说明.md')
        manifest = {'original_sha256': ORIGINAL_SHA256, 'runtime_url': RUNTIME_URL,
                    'runtime_archive_sha256': RUNTIME_SHA256,
                    'runtime_source': 'user-supplied; archive not reverified' if args.runtime else 'official download; SHA256 verified',
                    'changed_classes': sorted(CHANGED_CLASSES), 'business_operations_tested': False}
        (mac / 'build-info.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        if output.exists():
            raise RuntimeError('输出目录已被其他进程创建，停止发布本地结果')
        staging.rename(output)
        print('构建完成：' + str(output))
        print('尚未启动程序或连接服务器。请双击启动入口，并先在测试环境验证。')
    finally:
        if staging.exists():
            shutil.rmtree(staging)

if __name__ == '__main__':
    main()

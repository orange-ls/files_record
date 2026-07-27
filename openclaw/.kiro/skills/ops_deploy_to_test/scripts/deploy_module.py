#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo 模块远程部署脚本

功能：将本地 xc_addons 下的模块上传到远程 Linux 测试机，并重启服务。

用法：
    python deploy_module.py --project-root <项目根目录> <module_name> [--no-restart]

示例：
    python deploy_module.py --project-root C:\\Users\\15458\\Desktop\\xinchuang-materiel xc_dboms
    python deploy_module.py --project-root /path/to/project xc_dboms,xc_common
    python deploy_module.py --project-root /path/to/project xc_dboms --no-restart
"""
import argparse
import os
import stat
import sys
import time

import paramiko

# ============ 远程服务器配置 ============
REMOTE_HOST = '10.0.23.146'
REMOTE_PORT = 22
REMOTE_USER = 'root'
REMOTE_PASSWORD = 'Dcg!Xc#3146$'
REMOTE_PROJECT_PATH = '/opt/xc-test/xc-odoo-test/xc_addons/'
REMOTE_SERVICE_NAME = 'xc-test.service'

# 上传时排除的目录和文件模式
EXCLUDE_DIRS = {'__pycache__', '.git', '.kiro', 'node_modules', '.idea', '.vscode'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.log'}


def create_ssh_client():
    """创建 SSH 连接"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=REMOTE_PASSWORD, timeout=10)
    return client


def should_exclude(name, is_dir=False):
    """判断文件/目录是否应该排除"""
    if is_dir:
        return name in EXCLUDE_DIRS
    _, ext = os.path.splitext(name)
    return ext in EXCLUDE_EXTENSIONS


def upload_directory(sftp, local_dir, remote_dir):
    """递归上传目录到远程服务器"""
    file_count = 0
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        sftp.mkdir(remote_dir)

    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"

        if os.path.isdir(local_path):
            if should_exclude(item, is_dir=True):
                continue
            file_count += upload_directory(sftp, local_path, remote_path)
        else:
            if should_exclude(item, is_dir=False):
                continue
            sftp.put(local_path, remote_path)
            file_count += 1

    return file_count


def remote_rmdir(sftp, remote_dir):
    """递归删除远程目录（先清空再删除，确保干净部署）"""
    try:
        items = sftp.listdir_attr(remote_dir)
    except FileNotFoundError:
        return

    for item in items:
        remote_path = f"{remote_dir}/{item.filename}"
        if stat.S_ISDIR(item.st_mode):
            remote_rmdir(sftp, remote_path)
        else:
            sftp.remove(remote_path)
    sftp.rmdir(remote_dir)


def deploy_module(local_addons_path, module_name, restart=True):
    """部署单个模块"""
    local_module_path = os.path.join(local_addons_path, module_name)
    remote_module_path = f"{REMOTE_PROJECT_PATH}/{module_name}"

    if not os.path.isdir(local_module_path):
        print(f"[错误] 本地模块目录不存在: {local_module_path}")
        return False

    print(f"[部署] 模块: {module_name}")
    print(f"  本地: {local_module_path}")
    print(f"  远程: {remote_module_path}")

    start_time = time.time()

    try:
        print(f"[连接] {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PORT} ...")
        client = create_ssh_client()
        sftp = client.open_sftp()

        print(f"[清理] 删除远程旧文件 ...")
        remote_rmdir(sftp, remote_module_path)

        print(f"[上传] 正在上传文件 ...")
        file_count = upload_directory(sftp, local_module_path, remote_module_path)
        elapsed = time.time() - start_time
        print(f"[完成] 已上传 {file_count} 个文件，耗时 {elapsed:.1f}s")

        if restart:
            print(f"[重启] systemctl restart {REMOTE_SERVICE_NAME} ...")
            stdin, stdout, stderr = client.exec_command(f"systemctl restart {REMOTE_SERVICE_NAME}")
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print(f"[成功] 服务已重启")
            else:
                err = stderr.read().decode().strip()
                print(f"[警告] 重启返回码 {exit_code}: {err}")

        sftp.close()
        client.close()
        return True

    except Exception as e:
        print(f"[错误] 部署失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Odoo 模块远程部署工具')
    parser.add_argument('modules', help='模块名，多个用逗号分隔（如 xc_sn,xc_common）')
    parser.add_argument('--project-root', required=True, help='项目根目录路径')
    parser.add_argument('--no-restart', action='store_true', help='上传后不重启服务')
    args = parser.parse_args()

    local_addons_path = os.path.join(args.project_root, 'xc_addons')
    module_names = [m.strip() for m in args.modules.split(',') if m.strip()]

    if not module_names:
        print("[错误] 请指定至少一个模块名")
        sys.exit(1)

    print(f"{'=' * 50}")
    print(f"  Odoo 模块远程部署")
    print(f"  目标: {REMOTE_USER}@{REMOTE_HOST}")
    print(f"  模块: {', '.join(module_names)}")
    print(f"{'=' * 50}")

    all_success = True
    for module_name in module_names:
        success = deploy_module(local_addons_path, module_name, restart=False)
        if not success:
            all_success = False
            break

    if all_success and not args.no_restart:
        try:
            print(f"\n[重启] systemctl restart {REMOTE_SERVICE_NAME} ...")
            client = create_ssh_client()
            stdin, stdout, stderr = client.exec_command(f"systemctl restart {REMOTE_SERVICE_NAME}")
            exit_code = stdout.channel.recv_exit_status()
            if exit_code == 0:
                print(f"[成功] 服务已重启")
            else:
                err = stderr.read().decode().strip()
                print(f"[警告] 重启返回码 {exit_code}: {err}")
            client.close()
        except Exception as e:
            print(f"[错误] 重启失败: {e}")

    if all_success:
        print(f"\n{'=' * 50}")
        print(f"  部署完成！")
        print(f"{'=' * 50}")
    else:
        print(f"\n[失败] 部署过程中出现错误")
        sys.exit(1)


if __name__ == '__main__':
    main()

import shutil
import os
import win32gui
import time
import re
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from pathlib import Path
import win32com.client

def copy_folder_file(source_folder, destination_folder):
    """复制目标文件夹中的所有文件夹到另一文件夹"""

    # 获取源文件夹中的所有文件
    files = os.listdir(source_folder)

    # 遍历文件夹中的文件并复制Excel文件到目标文件夹
    for file in files:
        source_file = os.path.join(source_folder, file)
        destination_file = os.path.join(destination_folder, file)

        # 检查文件是否为Excel文件
        if file.endswith('.xlsx') or file.endswith('.xls'):
            # 复制文件到目标文件夹，并覆盖同名文件
            shutil.copy(source_file, destination_file)
            print(f'{file} 已成功复制到目标文件夹并覆盖同名文件！')

    print('指定文件夹中的Excel文件已成功复制到目标文件夹并覆盖同名文件！')


def clear_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


def create_folder(folder):
    # 检查文件夹是否存在
    if not os.path.exists(folder):
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(folder)
        print(f'文件夹 {folder} 创建成功！')
    else:
        print(f'文件夹 {folder} 已经存在！')


"""uiBot使用，运行时备份"""


def bak(share_folder, timedate_folder):
    # 获取源文件夹中的所有文件夹和文件
    items = os.listdir(share_folder)

    # 遍历源文件夹中的所有文件夹和文件
    for item in items:
        # 源文件或文件夹的完整路径
        source_path = os.path.join(share_folder, item)

        # 目标文件或文件夹的完整路径
        target_path = os.path.join(timedate_folder, item)

        # 如果是文件夹，则使用shutil.copytree()方法复制文件夹
        if os.path.isdir(source_path):
            if "历史数据" not in source_path:
                shutil.copytree(source_path, target_path)
        # 如果是文件，则使用shutil.copy2()方法复制文件
        else:
            shutil.copy2(source_path, target_path)


def delete_key_word_file(key_word, folder_path):
    """删除文件夹中文件名包含指定关键词的文件"""
    for filename in os.listdir(folder_path):
        if key_word in filename:
            file_path = os.path.join(folder_path, filename)
            os.remove(file_path)


def check_file_exist(key_word, folder_path):
    """检查文件夹中是否有文件名包含指定关键词的zip文件"""
    files_with_keyword = []

    for filename in os.listdir(folder_path):
        if (key_word in filename) and ("zip" in filename):
            files_with_keyword.append(filename)

    if len(files_with_keyword) > 0:
        print(f'Files with keyword "{key_word}" found:')
        return True
    else:
        print(f'No files with keyword "{key_word}" found.')
        return False


def check_file_exist_02(key_word, folder_path):
    """检查文件夹中是否有文件名包含指定关键词的文件"""
    files_with_keyword = []

    for filename in os.listdir(folder_path):
        if key_word in filename:
            files_with_keyword.append(filename)

    if len(files_with_keyword) > 0:
        print(f'Files with keyword "{key_word}" found:')
        return True
    else:
        print(f'No files with keyword "{key_word}" found.')
        return False


def copy_key_word_file(keyword, source_folder, target_folder):
    """复制目标文件夹中的带有指定关键字的文件 到另一文件夹"""
    # 确保目标文件夹存在
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # 遍历目标文件夹中的所有文件
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if keyword in file:
                # 构造源文件和目标文件的路径
                source_file = os.path.join(root, file)
                target_file = os.path.join(target_folder, file)

                # 复制文件
                shutil.copy(source_file, target_file)
                print(f'复制文件: {source_file} 到 {target_file}')

def copy_key_word_file_02(keyword, source_folder, target_folder):
    """复制目标文件夹中的带有指定关键字的文件 到另一文件夹，不包括目标文件夹中的子文件夹中的文件"""
    # 获取文件夹下的所有文件和文件夹名称
    filenames = os.listdir(source_folder)
    # 过滤出非文件夹的文件名
    file_names_only = [f for f in filenames if os.path.isfile(os.path.join(source_folder, f))]

    for file in file_names_only:
        if keyword in file:
            # 构造源文件和目标文件的路径
            source_file = os.path.join(source_folder, file)
            target_file = os.path.join(target_folder, file)

            # 复制文件
            shutil.copy(source_file, target_file)
            print(f'复制文件: {source_file} 到 {target_file}')


def return_key_word_file_name(keyword_list, source_folder):
    """返回目标文件夹中的带有指定关键字的文件的完整文件名"""
    name = ""
    path = ""

    # 获取文件夹下的所有文件和文件夹名称
    filenames = os.listdir(source_folder)
    # 过滤出非文件夹的文件名
    file_names_only = [f for f in filenames if os.path.isfile(os.path.join(source_folder, f))]

    # 遍历目标文件夹中的所有文件

    for file in file_names_only:
        if check_string_contains_all_values(file,keyword_list):
            path = os.path.join(source_folder, file)
            name = file
            break

    return {"name": name, "path": path}


def regex_key_word_file(pattern,folder):
    """返回目标文件夹中的符合正则的文件的完整文件名"""
    pass


def find_files_in_folder(keyword, folder):
    """返回文件夹中带有指定关键字的文件的名称"""
    file_names = []

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder):
        for file in files:
            # 检查文件名是否包含关键字
            if keyword in file:
                file_names.append(file)

    return file_names

def find_files_path_in_folder(keyword, folder):
    """返回文件夹中带有指定关键字的文件完整路径"""
    file_paths = []

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder):
        for file in files:
            # 检查文件名是否包含关键字
            if keyword in file:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)

    return file_paths

def find_files_path_format_in_folder(keyword, format,folder):
    """返回文件夹中带有指定关键字的文件完整路径"""
    file_paths = []

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder):
        for file in files:
            # 检查文件名是否包含关键字
            if (keyword in file) and (format in file):
                file_path = os.path.join(root, file)
                file_paths.append(file_path)

    return file_paths

def check_file_format_exist(key_word, folder_path, format):
    """检查文件夹中是否有文件名包含指定关键词的特定后缀的文件"""
    files_with_keyword = []

    for filename in os.listdir(folder_path):
        if (key_word in filename) and (format in filename):
            files_with_keyword.append(filename)

    if len(files_with_keyword) > 0:
        print(f'Files with keyword "{key_word}" found:')
        return True
    else:
        print(f'No files with keyword "{key_word}" found.')
        return False


def get_all_windows():
    windows = []

    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
        return True

    win32gui.EnumWindows(callback, windows)

    return windows


def get_window_title():
    window_titles = []
    windows = get_all_windows()
    for hwnd in windows:
        window_titles.append(win32gui.GetWindowText(hwnd))

    return window_titles


def judge_key_word_list(key_word, list):
    return any(key_word in element for element in list)


def check_string_contains_all_values(input_string, input_list):
    for item in input_list:
        if item not in input_string:
            return False
    return True

def keep_chinese(text):
    chinese_pattern = re.compile(r'[\u4e00-\u9fa5]')  # 匹配所有汉字的正则表达式
    result = re.findall(chinese_pattern, text)
    return ''.join(result)

def format_date(format_str='%Y-%#m-%#d'):
    # 获取当前日期
    now = datetime.now()

    # 格式化日期
    formatted_date = now.strftime(format_str)

    return formatted_date

def format_add_data(num):
    """返回当前日期+num天"""
    # 获取当前日期
    now = datetime.now()
    # 计算当前日期加上 num 天后的日期
    new_date = now + relativedelta(days=num)
    # 格式化日期
    formatted_date = new_date.strftime('%Y-%#m-%#d')
    return formatted_date

def format_last_year_date(format_str='%Y-%#m-%#d'):
    # 获取当前日期
    now = datetime.now()

    # 获取去年今天的日期
    last_year_today = now - relativedelta(years=1)
    
    # 格式化日期
    formatted_date = last_year_today.strftime(format_str)

    return formatted_date

def is_file_downloaded(keyword, download_folder, check_interval=5, max_checks=12):
    """
    判断 download 文件夹下是否下载完成了包含特定关键字的文件。

    参数:
    keyword (str): 要查找的特定关键字
    download_folder (str): 下载文件夹的路径
    check_interval (int): 检查文件大小变化的时间间隔（秒），默认为 5 秒
    max_checks (int): 最大检查次数，默认为 12 次

    返回:
    bool: 如果下载完成则返回 True，否则返回 False
    """
    for _ in range(max_checks):
        for root, _, files in os.walk(download_folder):
            for file in files:
                if keyword in file:
                    file_path = os.path.join(root, file)
                    initial_size = os.path.getsize(file_path)
                    time.sleep(check_interval)
                    new_size = os.path.getsize(file_path)
                    if initial_size == new_size:
                        return True
        time.sleep(check_interval)
    return False


def copy_file_to_path_with_new_name(source_file, target_dir, new_name=None):
    """
    复制文件到指定路径，并可选择修改文件名

    参数:
    source_file (str): 源文件的完整路径
    target_dir (str): 目标文件夹的路径
    new_name (str, optional): 新的文件名，如果为 None 则使用原文件名

    返回:
    str: 复制后文件的完整路径，如果复制失败则返回空字符串
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    if new_name is None:
        new_name = os.path.basename(source_file)
    
    target_file = os.path.join(target_dir, new_name)
    try:
        shutil.copy2(source_file, target_file)
        print(f"文件 {source_file} 已成功复制到 {target_file}")
        return target_file
    except Exception as e:
        print(f"复制文件时出现错误: {e}")
        return f"复制文件时出现错误: {e}"


def rename_folder_name(old_folder_path, new_folder_path):
    os.rename(old_folder_path, new_folder_path)


def list_split_keyword(name_list,key_word,split_key="--"):
    list = []
    for file_name in name_list:
        if "红字" not in file_name:
            continue
        temp = file_name.split(split_key)[1]
        if temp == key_word:
            list.append("\""+file_name+"\"")
    return " ".join(list)

def list_split_keyword_01(name_list,key_word,split_key="--"):
    list = []
    for file_name in name_list:
        if "红字" in file_name:
            continue
        temp = file_name.split(split_key)[1]
        temp = temp.split(".")[0]
        if temp == key_word:
            list.append("\""+file_name+"\"")
    return " ".join(list)


def list_split_by_num(input_list, group_size=8):
     return [input_list[i:i + group_size] for i in range(0, len(input_list), group_size)]


def is_difference_within_threshold(num1, num2, threshold=0.05):
    """
    判断两个数字的差的绝对值是否小于等于指定阈值。

    参数:
    num1 (int/float): 第一个数字。
    num2 (int/float): 第二个数字。
    threshold (float): 阈值，默认为 0.05。

    返回:
    bool: 如果差值的绝对值小于等于阈值，返回 True；否则返回 False。
    """
    diff = abs(num1 - num2)
    return diff <= threshold

def get_excel_sheet_names(file_path):
    """
    获取 Excel 文件中所有工作表的名称。

    :param file_path: Excel 文件的路径
    :return: 包含所有工作表名称的列表
    """
    try:
        # 使用 ExcelFile 类读取 Excel 文件
        xls = pd.ExcelFile(file_path)
        # 使用 sheet_names 属性获取所有工作表的名称
        sheet_names = xls.sheet_names
        return sheet_names
    except Exception as e:
        print(f"读取 Excel 文件时出错: {e}")
        return []


def dict_to_json(data,file_path):
    try:
        # 以写入模式打开文件
        with open(file_path, "w", encoding="utf-8") as f:
            # 将字典写入文件，禁用 ASCII 编码转换并设置缩进为 4 以提高可读性
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"字典已成功生成到 {file_path}")
    except Exception as e:
        print(f"生成 JSON 文件时出错: {e}")

def json_to_dict(file_path):
    """
    读取 JSON 文件并将其内容转换为 Python 字典。

    :param file_path: JSON 文件的路径
    :return: 包含 JSON 数据的 Python 字典，如果读取失败则返回空字典
    """
    try:
        # 以只读模式打开 JSON 文件，指定编码为 utf-8
        with open(file_path, 'r', encoding='utf-8') as file:
            # 使用 json.load 函数将文件内容转换为 Python 字典
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
    except json.JSONDecodeError:
        print(f"文件 {file_path} 不是有效的 JSON 格式。")
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
    return {}


def get_subdirectories_name(target_folder):
    """
    获取指定文件夹中的所有一级子文件夹，不包含子文件夹中的文件夹

    :param target_folder: 指定文件夹的路径
    :return: 包含所有一级子文件夹名称的列表

    """
    target_path = Path(target_folder)
    subdirectories = []
    try:
        subdirectories = [item.name for item in target_path.iterdir() if item.is_dir()]
    except Exception as e:
        print(f"获取一级子文件夹时出错: {e}")
    return subdirectories

def get_subdirectories_path(target_folder):
    """
    获取指定文件夹中的所有一级子文件夹，不包含子文件夹中的文件夹

    :param target_folder: 指定文件夹的路径
    :return: 包含所有一级子文件夹完整路径的列表

    """
    target_path = Path(target_folder)
    subdirectories = []
    try:
        # 修改为返回完整路径
        subdirectories = [str(item.resolve()) for item in target_path.iterdir() if item.is_dir()]
    except Exception as e:
        print(f"获取一级子文件夹时出错: {e}")
    return subdirectories


def table_trans_html(table_path,html_path):
    df = pd.read_excel(table_path)
    df.to_html(html_path,header=True,index=False)
    html_text = ""
    with open(html_path,"r",encoding="utf-8") as file:
        html_text = file.read()
    return html_text



def get_latest_email():
    """连接Outlook，获取最新的邮件信息"""
    try:
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = outlook.GetDefaultFolder(6)  # 6表示收件箱
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)  # 按接收时间排序，降序
        latest_email = messages.GetFirst()

        if latest_email:
            print("主题:", latest_email.Subject)
            print("发件人:", latest_email.SenderName)
            print("收件时间:", latest_email.ReceivedTime)
            print("正文:", latest_email.Body)
        else:
            print("收件箱为空1。")
    except Exception as e:
        print(f"发生错误: {e}")





if __name__ == '__main__':
    # 1
    table_01_path = r"D:\RPA\37单制作\37_dan_zhi_zuo\doc\archive\20250811\37单制作模板-上传.xlsx"
    table_02_path = r"D:\RPA\37单制作\37_dan_zhi_zuo\doc\补发\37单制作模板-上传-补发.xlsx"
    # merge_same_table(table_01_path,table_02_path)
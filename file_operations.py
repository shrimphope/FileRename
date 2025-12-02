#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量文件名修改工具 - 文件操作核心模块"""

import os
import re
import datetime
import shutil
from typing import List, Tuple, Optional


class FileOperations:
    """文件操作核心类，提供各种文件重命名功能"""
    
    def get_files_in_directory(self, directory_path: str) -> List[Tuple[str, int, datetime.datetime]]:
        """
        获取目录中的所有文件信息
        
        Args:
            directory_path: 目录路径
            
        Returns:
            包含文件信息的列表，每项为 (文件路径, 文件大小, 修改时间) 元组
        """
        file_list = []
        
        try:
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                
                # 只处理文件，跳过目录
                if os.path.isfile(file_path):
                    # 获取文件大小（字节）
                    file_size = os.path.getsize(file_path)
                    
                    # 获取文件修改时间
                    modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    file_list.append((file_path, file_size, modified_time))
            
            # 按文件名排序
            file_list.sort(key=lambda x: x[0])
            
        except PermissionError as e:
            raise PermissionError(f"没有权限访问目录 '{directory_path}': {str(e)}")
        except Exception as e:
            raise Exception(f"读取目录内容时出错: {str(e)}")
        
        return file_list
    
    def add_prefix_suffix(self, file_path: str, prefix: str = "", suffix: str = "") -> str:
        """
        为文件名添加前缀和后缀
        
        Args:
            file_path: 文件路径
            prefix: 要添加的前缀
            suffix: 要添加的后缀（添加在扩展名之前）
            
        Returns:
            新的文件名（不包含路径）
        """
        directory, filename = os.path.split(file_path)
        name, ext = os.path.splitext(filename)
        
        # 添加前缀和后缀
        new_name = f"{prefix}{name}{suffix}{ext}"
        
        # 验证文件名合法性
        return self._validate_filename(new_name)
    
    def replace_string(self, file_path: str, find_str: str, replace_str: str, case_sensitive: bool = True) -> str:
        """
        替换文件名中的字符串
        
        Args:
            file_path: 文件路径
            find_str: 要查找的字符串
            replace_str: 要替换的字符串
            case_sensitive: 是否区分大小写
            
        Returns:
            新的文件名（不包含路径）
        """
        directory, filename = os.path.split(file_path)
        
        # 根据是否区分大小写执行替换
        if case_sensitive:
            new_filename = filename.replace(find_str, replace_str)
        else:
            # 不区分大小写替换
            pattern = re.compile(re.escape(find_str), re.IGNORECASE)
            new_filename = pattern.sub(replace_str, filename)
        
        # 验证文件名合法性
        return self._validate_filename(new_filename)
    
    def regex_replace(self, file_path: str, pattern: str, replace_str: str) -> str:
        """
        使用正则表达式替换文件名中的内容
        
        Args:
            file_path: 文件路径
            pattern: 正则表达式模式
            replace_str: 替换字符串
            
        Returns:
            新的文件名（不包含路径）
        """
        directory, filename = os.path.split(file_path)
        
        try:
            # 编译正则表达式
            regex = re.compile(pattern)
            
            # 执行替换
            new_filename = regex.sub(replace_str, filename)
            
            # 验证文件名合法性
            return self._validate_filename(new_filename)
            
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {str(e)}")
    
    def numbering_rename(self, file_path: str, prefix: str = "", suffix: str = "", 
                         start_num: int = 1, digits: int = 3) -> str:
        """
        使用序号重命名文件
        
        Args:
            file_path: 文件路径
            prefix: 序号前的前缀
            suffix: 序号后的后缀
            start_num: 起始序号
            digits: 序号数字位数
            
        Returns:
            新的文件名（不包含路径）
        """
        directory, filename = os.path.split(file_path)
        _, ext = os.path.splitext(filename)
        
        # 格式化序号
        num_format = f"{{:0{digits}d}}"
        formatted_num = num_format.format(start_num)
        
        # 构建新文件名
        new_filename = f"{prefix}{formatted_num}{suffix}{ext}"
        
        # 验证文件名合法性
        return self._validate_filename(new_filename)
    
    def rename_file(self, file_path: str, new_name: str, target_dir: Optional[str] = None) -> bool:
        """
        执行文件重命名操作，可以指定目标文件夹
        
        Args:
            file_path: 原始文件路径
            new_name: 新的文件名（不包含路径）
            target_dir: 目标文件夹路径，如果为None则在原目录重命名
            
        Returns:
            重命名是否成功
        """
        if target_dir is None:
            directory = os.path.dirname(file_path)
        else:
            # 确保目标目录存在
            if not os.path.exists(target_dir):
                raise FileNotFoundError(f"目标文件夹 '{target_dir}' 不存在")
            if not os.path.isdir(target_dir):
                raise NotADirectoryError(f"'{target_dir}' 不是有效的目录")
            directory = target_dir
            
        new_path = os.path.join(directory, new_name)
        
        # 检查新文件路径是否与原路径相同
        if os.path.abspath(file_path) == os.path.abspath(new_path):
            return True  # 文件名未变化，视为成功
        
        # 检查目标文件是否已存在
        if os.path.exists(new_path):
            raise FileExistsError(f"文件 '{new_name}' 已存在于目标文件夹")
        
        try:
            # 执行重命名或移动
            if target_dir is None or os.path.samefile(os.path.dirname(file_path), target_dir):
                # 同一目录下的重命名
                os.rename(file_path, new_path)
            else:
                # 不同目录间的复制和重命名
                shutil.copy2(file_path, new_path)  # 复制文件保留元数据
            return True
        except PermissionError:
            raise PermissionError(f"没有权限操作文件 '{os.path.basename(file_path)}'")
        except OSError as e:
            raise OSError(f"重命名/移动文件时出错: {str(e)}")
    
    def _validate_filename(self, filename: str) -> str:
        """
        验证文件名的合法性，处理特殊字符
        
        Args:
            filename: 文件名
            
        Returns:
            处理后的合法文件名
        """
        # 检查文件名长度
        if len(filename) > 255:
            # 截断文件名，但保留扩展名
            name, ext = os.path.splitext(filename)
            max_name_length = 255 - len(ext)
            filename = f"{name[:max_name_length]}{ext}"
        
        # 检查并替换Windows系统中不允许的字符
        invalid_chars = '"*:<>?|/\\'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 检查文件名是否为空
        if not filename or filename.isspace():
            filename = "unnamed"
        
        # 检查文件名是否仅包含点或空格
        while filename.startswith('.'):
            filename = filename[1:] or "unnamed"
        
        # 检查保留文件名
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 
                         'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                         'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            filename = f"{filename}_renamed"
        
        return filename
    
    def check_file_permissions(self, file_path: str) -> bool:
        """
        检查文件是否有读写权限
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否有足够权限
        """
        return os.access(file_path, os.R_OK) and os.access(file_path, os.W_OK)
    
    def batch_rename(self, file_mappings: List[Tuple[str, str]], target_dir: Optional[str] = None) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        """
        批量重命名文件，可以指定目标文件夹
        
        Args:
            file_mappings: 文件映射列表，每项为 (原路径, 新名称) 元组
            target_dir: 目标文件夹路径，如果为None则在原目录重命名
            
        Returns:
            (成功列表, 失败列表)，每个列表包含 (原路径, 新路径) 或 (原路径, 错误信息) 元组
        """
        successes = []
        failures = []
        
        # 验证目标文件夹
        if target_dir is not None:
            if not os.path.exists(target_dir):
                raise FileNotFoundError(f"目标文件夹 '{target_dir}' 不存在")
            if not os.path.isdir(target_dir):
                raise NotADirectoryError(f"'{target_dir}' 不是有效的目录")
        
        # 第一遍检查：检查所有目标文件是否存在
        target_files = set()
        for file_path, new_name in file_mappings:
            if target_dir is None:
                directory = os.path.dirname(file_path)
            else:
                directory = target_dir
                
            new_path = os.path.join(directory, new_name)
            
            if new_path in target_files:
                failures.append((file_path, "目标文件名冲突"))
                continue
            
            if os.path.exists(new_path) and os.path.abspath(file_path) != os.path.abspath(new_path):
                failures.append((file_path, "目标文件已存在"))
                continue
            
            target_files.add(new_path)
        
        # 第二遍执行：实际执行重命名或移动
        for file_path, new_name in file_mappings:
            # 跳过已标记为失败的文件
            if any(f[0] == file_path for f in failures):
                continue
            
            try:
                success = self.rename_file(file_path, new_name, target_dir)
                if success:
                    if target_dir is None:
                        directory = os.path.dirname(file_path)
                    else:
                        directory = target_dir
                    new_path = os.path.join(directory, new_name)
                    successes.append((file_path, new_path))
            except Exception as e:
                failures.append((file_path, str(e)))
        
        return successes, failures
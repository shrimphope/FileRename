#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""撤销管理器模块"""

import os
import time
from collections import deque


class UndoManager:
    """撤销管理器，用于记录并重做/撤销文件重命名操作"""
    
    def __init__(self, max_history=50):
        """初始化撤销管理器
        
        Args:
            max_history: 最大历史记录数量，默认50
        """
        self.undo_stack = deque(maxlen=max_history)
        self.redo_stack = deque(maxlen=max_history)
        self.current_operation_id = 0
    
    def record_operation(self, rename_operations):
        """记录重命名操作
        
        Args:
            rename_operations: 重命名操作列表，每个元素为(old_path, new_path)
        """
        if not rename_operations:
            return
        
        # 生成操作ID
        operation_id = f"{time.time():.6f}_{self.current_operation_id}"
        self.current_operation_id += 1
        
        # 记录操作信息
        operation_info = {
            'id': operation_id,
            'timestamp': time.time(),
            'operations': rename_operations,
            'description': f"批量重命名 {len(rename_operations)} 个文件"
        }
        
        # 添加到撤销栈
        self.undo_stack.append(operation_info)
        
        # 清空重做栈
        self.redo_stack.clear()
    
    def can_undo(self):
        """检查是否可以撤销
        
        Returns:
            bool: 是否可以撤销
        """
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """检查是否可以重做
        
        Returns:
            bool: 是否可以重做
        """
        return len(self.redo_stack) > 0
    
    def undo(self):
        """执行撤销操作
        
        Returns:
            list: 需要执行的重命名操作列表，用于恢复到之前状态
        """
        if not self.can_undo():
            return []
        
        # 获取上一个操作
        operation = self.undo_stack.pop()
        
        # 准备撤销操作（交换old_path和new_path）
        # 对于跨文件夹操作，确保目标目录存在
        undo_operations = []
        for old_path, new_path in operation['operations']:
            # 对于撤销操作，我们要恢复到原始状态，所以old_path现在是目标路径
            # 确保目标目录存在
            target_dir = os.path.dirname(new_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # 添加到撤销操作列表（注意交换顺序）
            undo_operations.append((new_path, old_path))
        
        # 保存到重做栈
        self.redo_stack.append(operation)
        
        return undo_operations
    
    def redo(self):
        """执行重做操作
        
        Returns:
            list: 需要执行的重命名操作列表，用于重新应用之前的更改
        """
        if not self.can_redo():
            return []
        
        # 获取重做操作
        operation = self.redo_stack.pop()
        
        # 确保目标目录存在
        redo_operations = []
        for old_path, new_path in operation['operations']:
            # 对于重做操作，new_path是目标路径
            target_dir = os.path.dirname(new_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            redo_operations.append((old_path, new_path))
        
        # 保存到撤销栈
        self.undo_stack.append(operation)
        
        return redo_operations
    
    def get_undo_description(self):
        """获取下一个撤销操作的描述
        
        Returns:
            str: 撤销操作描述
        """
        if self.can_undo():
            return self.undo_stack[-1]['description']
        return ""
    
    def get_redo_description(self):
        """获取下一个重做操作的描述
        
        Returns:
            str: 重做操作描述
        """
        if self.can_redo():
            return self.redo_stack[-1]['description']
        return ""
    
    def clear_history(self):
        """清除所有历史记录"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_operation_id = 0
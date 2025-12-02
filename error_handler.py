#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量文件名修改工具 - 错误处理模块"""

import logging
import traceback
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QObject


class ErrorHandler(QObject):
    """错误处理器类，用于统一处理和显示各种错误信息"""
    
    def __init__(self):
        super().__init__()
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志记录配置"""
        # 配置基本的日志记录
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='file_rename_errors.log',
            filemode='a'
        )
        
        self.logger = logging.getLogger('FileRenameTool')
    
    def show_error(self, title: str, message: str):
        """
        显示错误消息对话框
        
        Args:
            title: 错误对话框标题
            message: 错误消息内容
        """
        # 记录到日志
        self.logger.error(f"{title}: {message}")
        
        # 显示错误对话框
        QMessageBox.critical(
            QApplication.activeWindow(),
            title,
            message,
            QMessageBox.Ok
        )
    
    def show_warning(self, title: str, message: str):
        """
        显示警告消息对话框
        
        Args:
            title: 警告对话框标题
            message: 警告消息内容
        """
        # 记录到日志
        self.logger.warning(f"{title}: {message}")
        
        # 显示警告对话框
        QMessageBox.warning(
            QApplication.activeWindow(),
            title,
            message,
            QMessageBox.Ok
        )
    
    def show_info(self, title: str, message: str):
        """
        显示信息消息对话框
        
        Args:
            title: 信息对话框标题
            message: 信息消息内容
        """
        # 显示信息对话框
        QMessageBox.information(
            QApplication.activeWindow(),
            title,
            message,
            QMessageBox.Ok
        )
    
    def ask_question(self, title: str, message: str) -> bool:
        """
        显示确认对话框，返回用户的选择
        
        Args:
            title: 对话框标题
            message: 消息内容
            
        Returns:
            True表示用户确认，False表示用户取消
        """
        reply = QMessageBox.question(
            QApplication.activeWindow(),
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    def handle_exception(self, exception: Exception, context: str = ""):
        """
        处理异常，显示详细错误信息
        
        Args:
            exception: 捕获的异常对象
            context: 错误发生的上下文信息
        """
        # 获取详细的异常信息
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()
        
        # 记录到日志
        log_message = f"{context}\n{error_type}: {error_message}\n{stack_trace}"
        self.logger.error(log_message)
        
        # 显示简化的错误信息给用户
        display_message = f"{context}\n\n错误类型: {error_type}\n错误信息: {error_message}\n\n详细信息已记录到日志文件。"
        
        QMessageBox.critical(
            QApplication.activeWindow(),
            "程序错误",
            display_message,
            QMessageBox.Ok
        )
    
    def validate_input(self, conditions: dict) -> tuple:
        """
        验证输入条件，返回验证结果
        
        Args:
            conditions: 条件字典，键为条件描述，值为布尔值
            
        Returns:
            (是否通过验证, 错误消息)
        """
        for description, is_valid in conditions.items():
            if not is_valid:
                return False, description
        
        return True, ""
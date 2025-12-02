#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量文件名修改工具 - 图形用户界面模块"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, 
    QLineEdit, QComboBox, QTreeWidget, QTreeWidgetItem, QFileDialog, QGroupBox,
    QFormLayout, QSpinBox, QDateTimeEdit, QCheckBox, QTabWidget, QMessageBox,
    QSplitter, QProgressBar, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal, QThread
from PyQt5.QtGui import QFont

from file_operations import FileOperations
from error_handler import ErrorHandler
from undo_manager import UndoManager


class FileRenameThread(QThread):
    """文件重命名操作线程类"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(list, list)
    error = pyqtSignal(str)
    
    def __init__(self, file_ops, files_to_rename, rename_params, target_dir=None):
        super().__init__()
        self.file_ops = file_ops
        self.files_to_rename = files_to_rename
        self.rename_params = rename_params
        self.target_dir = target_dir
    
    def run(self):
        try:
            results = []
            errors = []
            total = len(self.files_to_rename)
            
            for i, (file_path, new_name) in enumerate(self.files_to_rename):
                try:
                    success = self.file_ops.rename_file(file_path, new_name, self.target_dir)
                    if success:
                        results.append((file_path, new_name))
                    else:
                        errors.append((file_path, "重命名失败"))
                except Exception as e:
                    errors.append((file_path, str(e)))
                
                # 发送进度信号
                progress_value = int((i + 1) / total * 100)
                self.progress.emit(progress_value)
            
            self.finished.emit(results, errors)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.file_ops = FileOperations()
        self.error_handler = ErrorHandler()
        self.undo_manager = UndoManager()
        self.selected_folder = ""
        self.target_folder = ""  # 目标文件夹路径
        self.file_list = []
        self.filtered_files = []
        self.preview_list = []  # 存储预览的文件名映射
        self.history = []  # 存储操作历史，用于撤销功能
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("批量文件名修改工具")
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 1. 文件夹选择区域
        folder_group = QGroupBox("选择文件夹")
        folder_layout = QVBoxLayout()
        
        # 源文件夹选择
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("源文件夹:"))
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setReadOnly(True)
        source_layout.addWidget(self.folder_path_edit)
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_folder)
        source_layout.addWidget(browse_button)
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_file_list)
        source_layout.addWidget(refresh_button)
        
        # 目标文件夹选择
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("目标文件夹:"))
        self.target_folder_edit = QLineEdit()
        self.target_folder_edit.setReadOnly(True)
        target_layout.addWidget(self.target_folder_edit)
        target_browse_button = QPushButton("浏览...")
        target_browse_button.clicked.connect(self.browse_target_folder)
        target_layout.addWidget(target_browse_button)
        use_same_dir_checkbox = QCheckBox("与源文件夹相同")
        use_same_dir_checkbox.setChecked(True)
        use_same_dir_checkbox.stateChanged.connect(self.toggle_target_folder)
        target_layout.addWidget(use_same_dir_checkbox)
        
        folder_layout.addLayout(source_layout)
        folder_layout.addLayout(target_layout)
        folder_group.setLayout(folder_layout)
        
        # 2. 文件筛选区域
        filter_group = QGroupBox("文件筛选")
        filter_layout = QGridLayout()
        
        # 文件类型筛选
        filter_layout.addWidget(QLabel("文件类型:"), 0, 0)
        self.file_type_edit = QLineEdit()
        self.file_type_edit.setPlaceholderText("例如: .txt,.jpg 或留空不筛选")
        filter_layout.addWidget(self.file_type_edit, 0, 1)
        
        # 文件大小筛选
        filter_layout.addWidget(QLabel("最小文件大小 (KB):"), 1, 0)
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 1000000)
        self.min_size_spin.setValue(0)
        filter_layout.addWidget(self.min_size_spin, 1, 1)
        
        filter_layout.addWidget(QLabel("最大文件大小 (KB):"), 1, 2)
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(0, 1000000)
        self.max_size_spin.setValue(1000000)
        filter_layout.addWidget(self.max_size_spin, 1, 3)
        
        # 修改日期筛选
        filter_layout.addWidget(QLabel("修改日期范围:"), 2, 0)
        self.date_from_edit = QDateTimeEdit()
        self.date_from_edit.setDateTime(QDateTime.currentDateTime().addDays(-30))
        self.date_from_edit.setCalendarPopup(True)
        filter_layout.addWidget(self.date_from_edit, 2, 1)
        
        filter_layout.addWidget(QLabel("至:"), 2, 2)
        self.date_to_edit = QDateTimeEdit()
        self.date_to_edit.setDateTime(QDateTime.currentDateTime())
        self.date_to_edit.setCalendarPopup(True)
        filter_layout.addWidget(self.date_to_edit, 2, 3)
        
        # 应用筛选按钮
        apply_filter_button = QPushButton("应用筛选")
        apply_filter_button.clicked.connect(self.apply_filters)
        filter_layout.addWidget(apply_filter_button, 3, 0, 1, 4)
        
        filter_group.setLayout(filter_layout)
        
        # 3. 重命名设置区域 - 使用选项卡
        rename_tab_widget = QTabWidget()
        
        # 3.1 添加前缀/后缀选项卡
        prefix_suffix_widget = QWidget()
        prefix_suffix_layout = QFormLayout()
        
        self.prefix_edit = QLineEdit()
        self.suffix_edit = QLineEdit()
        
        prefix_suffix_layout.addRow("前缀:", self.prefix_edit)
        prefix_suffix_layout.addRow("后缀:", self.suffix_edit)
        
        prefix_suffix_widget.setLayout(prefix_suffix_layout)
        rename_tab_widget.addTab(prefix_suffix_widget, "添加前缀/后缀")
        
        # 3.2 替换字符串选项卡
        replace_widget = QWidget()
        replace_layout = QFormLayout()
        
        self.find_edit = QLineEdit()
        self.replace_edit = QLineEdit()
        self.case_sensitive_check = QCheckBox("区分大小写")
        
        replace_layout.addRow("查找:", self.find_edit)
        replace_layout.addRow("替换为:", self.replace_edit)
        replace_layout.addRow(self.case_sensitive_check)
        
        replace_widget.setLayout(replace_layout)
        rename_tab_widget.addTab(replace_widget, "替换字符串")
        
        # 3.3 正则表达式选项卡
        regex_widget = QWidget()
        regex_layout = QFormLayout()
        
        self.regex_pattern_edit = QLineEdit()
        self.regex_replace_edit = QLineEdit()
        self.regex_check = QCheckBox("使用正则表达式")
        
        regex_layout.addRow("正则表达式:", self.regex_pattern_edit)
        regex_layout.addRow("替换为:", self.regex_replace_edit)
        
        regex_widget.setLayout(regex_layout)
        rename_tab_widget.addTab(regex_widget, "正则表达式")
        
        # 3.4 序号重命名选项卡
        numbering_widget = QWidget()
        numbering_layout = QFormLayout()
        
        self.numbering_prefix_edit = QLineEdit()
        self.numbering_suffix_edit = QLineEdit()
        self.start_number_spin = QSpinBox()
        self.start_number_spin.setRange(1, 9999)
        self.digits_spin = QSpinBox()
        self.digits_spin.setRange(1, 8)
        self.digits_spin.setValue(3)
        
        numbering_layout.addRow("前缀:", self.numbering_prefix_edit)
        numbering_layout.addRow("起始数字:", self.start_number_spin)
        numbering_layout.addRow("数字位数:", self.digits_spin)
        numbering_layout.addRow("后缀:", self.numbering_suffix_edit)
        
        numbering_widget.setLayout(numbering_layout)
        rename_tab_widget.addTab(numbering_widget, "序号重命名")
        
        # 重命名设置组
        rename_group = QGroupBox("重命名设置")
        rename_group_layout = QVBoxLayout()
        rename_group_layout.addWidget(rename_tab_widget)
        rename_group.setLayout(rename_group_layout)
        
        # 4. 文件列表和预览区域
        splitter = QSplitter(Qt.Vertical)
        
        # 4.1 原始文件列表
        original_files_group = QGroupBox("原始文件列表")
        original_files_layout = QVBoxLayout()
        
        self.original_files_tree = QTreeWidget()
        self.original_files_tree.setHeaderLabels(["文件名", "大小", "修改日期"])
        self.original_files_tree.setColumnWidth(0, 300)
        original_files_layout.addWidget(self.original_files_tree)
        
        original_files_group.setLayout(original_files_layout)
        
        # 4.2 预览文件列表
        preview_files_group = QGroupBox("预览修改结果")
        preview_files_layout = QVBoxLayout()
        
        self.preview_files_tree = QTreeWidget()
        self.preview_files_tree.setHeaderLabels(["原始文件名", "新文件名"])
        self.preview_files_tree.setColumnWidth(0, 300)
        self.preview_files_tree.setColumnWidth(1, 300)
        preview_files_layout.addWidget(self.preview_files_tree)
        
        preview_files_group.setLayout(preview_files_layout)
        
        splitter.addWidget(original_files_group)
        splitter.addWidget(preview_files_group)
        splitter.setSizes([300, 300])
        
        # 5. 操作按钮区域
        actions_layout = QHBoxLayout()
        
        preview_button = QPushButton("预览")
        preview_button.clicked.connect(self.preview_rename)
        
        apply_button = QPushButton("应用修改")
        apply_button.clicked.connect(self.apply_rename)
        
        undo_button = QPushButton("撤销")
        undo_button.clicked.connect(self.undo_rename)
        
        self.redo_button = QPushButton("重做")
        self.redo_button.clicked.connect(self.redo_rename)
        self.redo_button.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        actions_layout.addWidget(preview_button)
        actions_layout.addWidget(apply_button)
        actions_layout.addWidget(undo_button)
        actions_layout.addWidget(self.redo_button)
        actions_layout.addWidget(self.progress_bar)
        
        # 将所有部分添加到主布局
        main_layout.addWidget(folder_group)
        main_layout.addWidget(filter_group)
        main_layout.addWidget(rename_group)
        main_layout.addWidget(splitter)
        main_layout.addLayout(actions_layout)
    
    def browse_folder(self):
        """浏览并选择文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if folder_path:
            self.selected_folder = folder_path
            self.folder_path_edit.setText(folder_path)
            self.refresh_file_list()
    
    def refresh_file_list(self):
        """刷新文件列表"""
        if not self.selected_folder:
            return
        
        try:
            self.file_list = self.file_ops.get_files_in_directory(self.selected_folder)
            self.filtered_files = self.file_list.copy()
            self.update_original_files_tree()
        except Exception as e:
            self.error_handler.show_error("错误", f"无法读取文件夹内容: {str(e)}")
    
    def update_original_files_tree(self):
        """更新原始文件列表树"""
        self.original_files_tree.clear()
        
        for file_info in self.filtered_files:
            file_path, file_size, modified_time = file_info
            file_name = os.path.basename(file_path)
            
            item = QTreeWidgetItem([file_name, self.format_size(file_size), modified_time.strftime("%Y-%m-%d %H:%M:%S")])
            self.original_files_tree.addTopLevelItem(item)
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
    
    def apply_filters(self):
        """应用文件筛选条件"""
        if not self.file_list:
            return
        
        try:
            # 获取筛选条件
            file_types = [ft.strip().lower() for ft in self.file_type_edit.text().split(',') if ft.strip()]
            min_size_kb = self.min_size_spin.value()
            max_size_kb = self.max_size_spin.value()
            date_from = self.date_from_edit.dateTime().toPyDateTime()
            date_to = self.date_to_edit.dateTime().toPyDateTime()
            
            # 应用筛选
            self.filtered_files = []
            for file_info in self.file_list:
                file_path, file_size, modified_time = file_info
                
                # 转换为与筛选条件相同的单位
                file_size_kb = file_size / 1024
                
                # 文件类型筛选
                if file_types:
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext not in file_types:
                        continue
                
                # 文件大小筛选
                if not (min_size_kb <= file_size_kb <= max_size_kb):
                    continue
                
                # 修改日期筛选
                if not (date_from <= modified_time <= date_to):
                    continue
                
                self.filtered_files.append(file_info)
            
            self.update_original_files_tree()
        except Exception as e:
            self.error_handler.show_error("筛选错误", f"应用筛选条件时出错: {str(e)}")
    
    def preview_rename(self):
        """预览重命名结果"""
        if not self.filtered_files:
            self.error_handler.show_error("提示", "没有文件可以重命名")
            return
        
        try:
            self.preview_list = []
            current_tab = self.findChild(QTabWidget).currentIndex()
            
            # 根据当前选项卡获取重命名参数
            if current_tab == 0:  # 添加前缀/后缀
                prefix = self.prefix_edit.text()
                suffix = self.suffix_edit.text()
                
                for file_info in self.filtered_files:
                    file_path, _, _ = file_info
                    new_name = self.file_ops.add_prefix_suffix(file_path, prefix, suffix)
                    self.preview_list.append((file_path, new_name))
            
            elif current_tab == 1:  # 替换字符串
                find_str = self.find_edit.text()
                replace_str = self.replace_edit.text()
                case_sensitive = self.case_sensitive_check.isChecked()
                
                for file_info in self.filtered_files:
                    file_path, _, _ = file_info
                    new_name = self.file_ops.replace_string(file_path, find_str, replace_str, case_sensitive)
                    self.preview_list.append((file_path, new_name))
            
            elif current_tab == 2:  # 正则表达式
                pattern = self.regex_pattern_edit.text()
                replace_str = self.regex_replace_edit.text()
                
                for file_info in self.filtered_files:
                    file_path, _, _ = file_info
                    new_name = self.file_ops.regex_replace(file_path, pattern, replace_str)
                    self.preview_list.append((file_path, new_name))
            
            elif current_tab == 3:  # 序号重命名
                prefix = self.numbering_prefix_edit.text()
                suffix = self.numbering_suffix_edit.text()
                start_num = self.start_number_spin.value()
                digits = self.digits_spin.value()
                
                for i, file_info in enumerate(self.filtered_files):
                    file_path, _, _ = file_info
                    new_name = self.file_ops.numbering_rename(file_path, prefix, suffix, start_num + i, digits)
                    self.preview_list.append((file_path, new_name))
            
            # 更新预览列表
            self.update_preview_tree()
        except Exception as e:
            self.error_handler.show_error("预览错误", f"生成预览时出错: {str(e)}")
    
    def update_preview_tree(self):
        """更新预览文件列表树"""
        self.preview_files_tree.clear()
        
        for file_path, new_name in self.preview_list:
            original_name = os.path.basename(file_path)
            item = QTreeWidgetItem([original_name, new_name])
            self.preview_files_tree.addTopLevelItem(item)
    
    def apply_rename(self):
        """应用重命名操作"""
        if not self.preview_list:
            self.error_handler.show_error("提示", "请先预览重命名结果")
            return
        
        # 获取目标文件夹
        target_dir = self.target_folder if self.target_folder else None
        
        # 确认操作
        if target_dir:
            message = f"确定要将 {len(self.preview_list)} 个文件重命名并移动到目标文件夹吗？"
        else:
            message = f"确定要重命名 {len(self.preview_list)} 个文件吗？"
            
        reply = QMessageBox.question(
            self, "确认重命名", 
            message,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 检查文件名冲突
        conflicts = self.check_name_conflicts()
        if conflicts:
            conflict_msg = "发现文件名冲突:\n"
            for conflict in conflicts:
                conflict_msg += f"- {conflict}\n"
            self.error_handler.show_error("文件名冲突", conflict_msg)
            self.progress_bar.setVisible(False)
            return
        
        # 启动重命名线程
        self.rename_thread = FileRenameThread(
            self.file_ops, self.preview_list, {}, target_dir
        )
        self.rename_thread.progress.connect(self.update_progress)
        self.rename_thread.finished.connect(self.rename_finished)
        self.rename_thread.error.connect(self.rename_error)
        self.rename_thread.start()
    
    def check_name_conflicts(self):
        """检查重命名后是否有文件名冲突"""
        conflicts = []
        new_names = set()
        
        for _, new_name in self.preview_list:
            if new_name in new_names:
                conflicts.append(new_name)
            new_names.add(new_name)
        
        return conflicts
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def rename_finished(self, results, errors):
        """重命名完成后的处理"""
        self.progress_bar.setVisible(False)
        
        # 保存操作历史
        if results:
            self.history.append(results)
            # 记录到撤销管理器
            self.undo_manager.record_operation(results)
            self.update_undo_redo_buttons()
        
        # 显示结果
        if errors:
            error_msg = "部分文件重命名失败:\n"
            for file_path, error in errors[:5]:  # 只显示前5个错误
                error_msg += f"- {os.path.basename(file_path)}: {error}\n"
            if len(errors) > 5:
                error_msg += f"... 还有 {len(errors) - 5} 个错误\n"
            QMessageBox.warning(self, "重命名结果", 
                              f"成功重命名 {len(results)} 个文件\n{error_msg}")
        else:
            QMessageBox.information(self, "重命名结果", 
                                  f"成功重命名 {len(results)} 个文件")
        
        # 刷新文件列表
        self.refresh_file_list()
        self.preview_list = []
        self.preview_files_tree.clear()
    
    def rename_error(self, error_msg):
        """重命名出错处理"""
        self.progress_bar.setVisible(False)
        self.error_handler.show_error("重命名错误", f"重命名过程中出错: {error_msg}")
    
    def browse_target_folder(self):
        """浏览选择目标文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹", self.target_folder)
        if folder:
            self.target_folder = folder
            self.target_folder_edit.setText(folder)
    
    def toggle_target_folder(self, state):
        """切换是否使用与源文件夹相同的目标文件夹"""
        if state == Qt.Checked:
            self.target_folder = ""
            self.target_folder_edit.setText("")
            self.target_folder_edit.setEnabled(False)
        else:
            self.target_folder_edit.setEnabled(True)
            if self.selected_folder and not self.target_folder:
                self.target_folder = self.selected_folder
                self.target_folder_edit.setText(self.selected_folder)
    
    def undo_rename(self):
        """撤销上一次重命名操作"""
        if not self.undo_manager.can_undo():
            self.error_handler.show_error("提示", "没有可撤销的操作")
            return
        
        # 确认撤销
        reply = QMessageBox.question(
            self, "确认撤销", 
            "确定要撤销上一次重命名操作吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 从撤销管理器获取撤销操作
        undo_operations = self.undo_manager.undo()
        if not undo_operations:
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 启动撤销线程 - 撤销操作不需要指定目标文件夹
        self.undo_thread = FileRenameThread(
            self.file_ops, undo_operations, {}
        )
        self.undo_thread.progress.connect(self.update_progress)
        self.undo_thread.finished.connect(self.undo_finished)
        self.undo_thread.error.connect(self.undo_error)
        self.undo_thread.start()
    
    def undo_finished(self, results, errors):
        """撤销完成后的处理"""
        self.progress_bar.setVisible(False)
        
        # 显示结果
        if errors:
            error_msg = "部分文件撤销失败:\n"
            for file_path, error in errors[:5]:
                error_msg += f"- {os.path.basename(file_path)}: {error}\n"
            if len(errors) > 5:
                error_msg += f"... 还有 {len(errors) - 5} 个错误\n"
            QMessageBox.warning(self, "撤销结果", 
                              f"成功撤销 {len(results)} 个文件\n{error_msg}")
        else:
            QMessageBox.information(self, "撤销结果", 
                                  f"成功撤销 {len(results)} 个文件")
        
        # 刷新文件列表
        self.refresh_file_list()
    
    def undo_error(self, error_msg):
        """撤销出错处理"""
        self.progress_bar.setVisible(False)
        self.error_handler.show_error("撤销错误", f"撤销过程中出错: {error_msg}")
    
    def update_undo_redo_buttons(self):
        """更新撤销和重做按钮状态"""
        # 启用/禁用重做按钮
        self.redo_button.setEnabled(self.undo_manager.can_redo())
        
        # 更新按钮提示
        if self.undo_manager.can_redo():
            self.redo_button.setToolTip(f"重做: {self.undo_manager.get_redo_description()}")
        else:
            self.redo_button.setToolTip("")
    
    def redo_rename(self):
        """执行重做操作"""
        if not self.undo_manager.can_redo():
            return
        
        # 确认重做
        reply = QMessageBox.question(
            self, "确认重做", 
            "确定要重做上一次操作吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 获取重做操作
        redo_operations = self.undo_manager.redo()
        
        # 获取目标文件夹 - 重做操作使用当前设置的目标文件夹
        target_dir = self.target_folder if self.target_folder else None
        if not redo_operations:
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 启动重做线程
        self.redo_thread = FileRenameThread(
            self.file_ops, redo_operations, {}, target_dir
        )
        self.redo_thread.progress.connect(self.update_progress)
        self.redo_thread.finished.connect(self.redo_finished)
        self.redo_thread.error.connect(self.redo_error)
        self.redo_thread.start()
    
    def redo_finished(self, results, errors):
        """重做完成后的处理"""
        self.progress_bar.setVisible(False)
        
        # 更新撤销管理器
        self.update_undo_redo_buttons()
        
        # 显示结果
        if errors:
            error_msg = "部分文件重做失败:\n"
            for file_path, error in errors[:5]:
                error_msg += f"- {os.path.basename(file_path)}: {error}\n"
            if len(errors) > 5:
                error_msg += f"... 还有 {len(errors) - 5} 个错误\n"
            QMessageBox.warning(self, "重做结果", 
                              f"成功重做 {len(results)} 个文件\n{error_msg}")
        else:
            QMessageBox.information(self, "重做结果", 
                                  f"成功重做 {len(results)} 个文件")
        
        # 刷新文件列表
        self.refresh_file_list()
    
    def redo_error(self, error_msg):
        """重做出错处理"""
        self.progress_bar.setVisible(False)
        self.error_handler.show_error("重做错误", f"重做过程中出错: {error_msg}")
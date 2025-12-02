#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量文件名修改工具 - 主程序入口"""

import sys
import os

# 添加当前目录到Python路径，便于导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


def main():
    """主程序入口函数"""
    # 确保中文显示正常
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("批量文件名修改工具")
    app.setOrganizationName("FileRenameTools")
    
    # 创建并显示主窗口
    main_window = MainWindow()
    main_window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
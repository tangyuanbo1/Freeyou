from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QPixmap
import sys
import os

def display_png_image():
    app = QApplication(sys.argv)
    window = QMainWindow()

    # 获取PNG文件的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(current_dir, "logo4@4x.png")
    
    # 创建标签并设置图像
    label = QLabel()
    pixmap = QPixmap(png_path)
    label.setPixmap(pixmap)
    
    # 设置标签为主窗口的中心部件
    window.setCentralWidget(label)
    window.resize(pixmap.width(), pixmap.height())

    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    display_png_image() 
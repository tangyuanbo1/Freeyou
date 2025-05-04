from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PyQt5.QtSvg import QSvgWidget, QGraphicsSvgItem
import sys
import os

def display_svg_item():
    app = QApplication(sys.argv)
    window = QMainWindow()

    # 获取SVG文件的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(current_dir, "logo4.svg.fixed.svg")  # 使用修复版的SVG文件
    
    # 创建场景和SVG项目
    scene = QGraphicsScene()
    svg_item = QGraphicsSvgItem(svg_path)
    scene.addItem(svg_item)
    
    # 创建视图并设置场景
    view = QGraphicsView(scene, window)
    view.setSceneRect(svg_item.boundingRect())
    
    # 设置视图为主窗口的中心部件
    window.setCentralWidget(view)
    window.resize(800, 600)

    window.show()
    sys.exit(app.exec_())

def display_svg_widget():
    app = QApplication(sys.argv)
    window = QMainWindow()

    # 获取SVG文件的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(current_dir, "logo4.svg.fixed.svg")  # 使用修复版的SVG文件
    
    svg_widget = QSvgWidget(svg_path)
    window.setCentralWidget(svg_widget)

    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    display_svg_item()
    #display_svg_widget()

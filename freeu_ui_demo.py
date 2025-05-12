import sys
import os
import math
import signal
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFrame, QLabel, 
                            QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
                            QScrollArea, QWidget, QSizePolicy)
from PyQt5.QtGui import QPixmap, QFont, QColor, QPainter, QPainterPath, QBrush, QIcon, QPen, QFontDatabase, QMovie, QRegion
from PyQt5.QtCore import Qt, QSize, QRect, QRectF, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup, QObject, pyqtSignal, QThread, QThreadPool
import requests
import pyautogui
import psutil
import platform
# 根据平台有条件地导入
if platform.system() == 'Windows':
    import win32gui
    import win32process
from datetime import datetime

# 添加OpenAI客户端，用于向后端发送请求
from openai import OpenAI

class RoundedRectLabel(QLabel):
    def __init__(self, parent=None, radius=0):
        super().__init__(parent)
        self.radius = radius
        self.setStyleSheet("background-color: transparent;")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        rect = QRectF(0, 0, self.width(), self.height())
        path.addRoundedRect(rect, self.radius, self.radius)
        
        painter.setClipPath(path)
        super().paintEvent(event)

class ShadowFrame(QFrame):
    def __init__(self, parent=None, radius=0, shadow_blur=0, shadow_color=QColor(0, 0, 0, 80)):
        super().__init__(parent)
        self.radius = radius
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.radius > 0:
            path = QPainterPath()
            rect = QRectF(self.rect())
            path.addRoundedRect(rect, self.radius, self.radius)
            
            painter.setClipPath(path)
            super().paintEvent(event)
        else:
            super().paintEvent(event)

# 添加截图服务类
class ScreenshotService(QObject):
    message_received = pyqtSignal(str)  # 当收到消息时发出信号
    
    def __init__(self, api_url="http://127.0.0.1:5000/items/", screenshot_dir=None):
        super().__init__()
        self.api_url = api_url
        self.api_url = "http://60.205.253.233:5000/recording_video"
        self.api_url = "http://60.205.253.233:5000/analysis"
        
        # 设置截图保存目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if screenshot_dir:
            self.screenshot_dir = screenshot_dir
        else:
            # 使用sense_env/pic作为默认保存目录
            sense_env_dir = os.path.join(script_dir, "sense_env")
            self.screenshot_dir = os.path.join(sense_env_dir, "pic")
        
        self.is_requesting = False
        self.request_thread = None
        
        # 添加状态标志，用于交替执行截图和请求
        self.should_take_screenshot = True  # True表示下一次应该截图，False表示下一次应该发送请求
        self.last_screenshot_path = None    # 保存最近一次截图的路径
        
        # 确保目录存在
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
            
        # 确保sense_env的其他子目录也存在
        sense_env_dir = os.path.dirname(self.screenshot_dir)
        ocr_dir = os.path.join(sense_env_dir, "ocr")
        describe_dir = os.path.join(sense_env_dir, "describe")
        sense_dir = os.path.join(sense_env_dir, "sense")
        
        for directory in [ocr_dir, describe_dir, sense_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        print(f"截图服务初始化，目录: {self.screenshot_dir}")
    
    def take_screenshot_and_request(self):
        """截图和发送请求交替进行"""
        if self.is_requesting:
            return
            
        if self.should_take_screenshot:
            # 执行截图操作
            self._take_screenshot()
            # 切换状态，下一次将发送请求
            self.should_take_screenshot = False
        else:
            # 执行请求操作
            self.send_api_request()
            # 切换状态，下一次将截图
            self.should_take_screenshot = True
    
    def _take_screenshot(self):
        """只执行截图操作"""
        try:
            # 获取当前活动窗口的进程名称
            active_app = self.get_active_window_process_name()
            app_name = os.path.splitext(active_app)[0].lower().replace(" ", "_")
            
            # 保存截图
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(self.screenshot_dir, f"screenshot_{current_time}_{app_name}.png")
            
            screenshot = pyautogui.screenshot()
            screenshot.save(file_path)
            print(f"保存截图：{file_path}")
            
            # 保存最近的截图路径
            self.last_screenshot_path = file_path
        except Exception as e:
            print(f"截图错误: {e}")
            # 如果截图失败，重置标志以便下次重试
            self.should_take_screenshot = True
    
    def get_active_window_process_name(self):
        """获取当前活动窗口的进程名称，跨平台兼容"""
        try:
            # Windows平台
            if platform.system() == 'Windows':
                window = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(window)
                process = psutil.Process(pid)
                return process.name()
            # macOS平台
            elif platform.system() == 'Darwin':
                # 在Mac上，我们只能获取当前运行的所有进程
                # 然后返回当前应用的名称或一个默认名称
                try:
                    # 尝试使用applescript获取当前前台应用
                    import subprocess
                    cmd = "osascript -e 'tell application \"System Events\" to get name of first application process whose frontmost is true'"
                    process = subprocess.check_output(cmd, shell=True).decode().strip()
                    return process
                except:
                    # 如果无法获取，返回当前Python进程名称
                    return psutil.Process().name()
            # Linux和其他平台
            else:
                return psutil.Process().name()
        except:
            return "unknown_app"
    
    def send_api_request(self):
        """发送API请求"""
        if self.is_requesting:
            return
            
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.quit()
            self.request_thread.wait()
            
        self.is_requesting = True
        # 传递截图路径
        self.request_thread = APIRequestThread(self.api_url, self.last_screenshot_path)
        self.request_thread.finished.connect(self.handle_response)
        self.request_thread.start()
    
    def handle_response(self, result):
        """处理API响应"""
        self.is_requesting = False
        if isinstance(result, Exception):
            print(f"API请求错误: {result}")
        else:
            try:
                if result.status_code == 200:
                    response_data = result.json()
                    # 判断后端返回的数据是否为有意义的数据
                    print(f"收到消息: {response_data['message']}")
                    if response_data.get('message') and response_data['message'] != '0':
                        
                        self.message_received.emit(response_data['message'])
            except Exception as e:
                print(f"处理响应错误: {e}")

class APIRequestThread(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, api_url, image_path=None):
        super().__init__()
        self.api_url = api_url
        self.image_path = image_path
    
    def run(self):
        try:
            if self.image_path and os.path.exists(self.image_path):
                try:
                    with open(self.image_path, 'rb') as f:
                        files = {'file': (os.path.basename(self.image_path), f, 'image/png')}
                        response = requests.post(self.api_url, files=files, timeout=20)
                    self.finished.emit(response)
                except requests.exceptions.ConnectionError:
                    class MockResponse:
                        def __init__(self):
                            self.status_code = 200
                        def json(self):
                            return {"message": "这是一条测试消息，API服务器未连接"}
                    self.finished.emit(MockResponse())
            else:
                # 没有图片可上传
                class MockResponse:
                    def __init__(self):
                        self.status_code = 400
                    def json(self):
                        return {"message": "未找到截图文件，无法上传"}
                self.finished.emit(MockResponse())
        except Exception as e:
            self.finished.emit(e)

# 添加控制器以使用截图服务
class ScreenshotServiceController(QObject):
    """控制器类，负责监控截图服务的消息并通知视图"""
    def __init__(self, service, view):
        super().__init__()
        self.service = service
        self.view = view
        
        # 连接服务的消息信号到处理方法
        self.service.message_received.connect(self.on_message_received)
        print("已连接截图服务消息信号")
        
        # 连接视图的状态变化信号
        self.view.mode_changed.connect(self.on_mode_changed)
        print("已连接模式变化信号")
        
        # 创建截图监控定时器
        self.screenshot_timer = QTimer()
        self.screenshot_timer.timeout.connect(self.service.take_screenshot_and_request)
        
        # 根据初始状态决定是否启动定时器
        if self.view.current_mode == self.view.LOGO_MODE:
            self.screenshot_timer.start(1500)  # 每1.5秒检查一次
            print("初始状态为LOGO模式，启动截图定时器")
        else:
            self.screenshot_timer.stop()
            print("初始状态不是LOGO模式，不启动截图定时器")
            
            # 如果初始状态是MESSAGE模式，启动10秒定时器
            if self.view.current_mode == self.view.MESSAGE_MODE:
                print("初始状态为MESSAGE模式，启动10秒计时器")
                self.view.timer.start(10000)
        
        # 连接主窗口的关闭事件
        self.view.aboutToClose.connect(self.stop_all)
    
    def stop_all(self):
        """停止所有定时器和线程"""
        print("正在停止所有截图服务相关的定时器和线程...")
        if hasattr(self, 'screenshot_timer') and self.screenshot_timer.isActive():
            self.screenshot_timer.stop()
        
        # 停止服务中的线程
        if hasattr(self.service, 'request_thread') and self.service.request_thread and self.service.request_thread.isRunning():
            self.service.request_thread.quit()
            self.service.request_thread.wait(1000)  # 等待最多1秒
    
    def on_message_received(self, message):
        """收到服务消息时的响应"""
        print(f"收到消息: {message}, 当前模式: {self.view.current_mode}")
        
        # 清空消息列表
        self.view.messages.clear()
        
        # 添加新消息作为第一条
        self.view.messages.append({"sender": "agent", "content": message})
        
        # 处理不同模式下的UI更新
        if self.view.current_mode == self.view.LOGO_MODE:
            print("准备从LOGO模式切换到MESSAGE模式")
            self.view.exitLogoMode()
            # 在切换完成后确保将滚动条拉到顶部
            QTimer.singleShot(500, lambda: self.scroll_message_to_top())
        elif self.view.current_mode == self.view.CHAT_MODE:
            # 在CHAT模式下，重新加载消息列表显示
            print("在CHAT模式下刷新消息显示")
            self.view.reloadMessages()
        elif self.view.current_mode == self.view.MESSAGE_MODE:
            # 在MESSAGE模式下，刷新简化消息显示
            print("在MESSAGE模式下刷新消息显示")
            if hasattr(self.view, 'message_chat_layout') and self.view.message_chat_layout:
                # 清除现有消息
                while self.view.message_chat_layout.count() > 1:  # 保留最后一个stretch
                    item = self.view.message_chat_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                
                # 重新添加简化消息
                self.view.addSimplifiedMessage()
                
                # 将滚动条拉到顶部
                QTimer.singleShot(100, lambda: self.scroll_message_to_top())
        
        # 打印处理后的消息列表内容
        print("===== 消息列表内容 =====")
        for i, msg in enumerate(self.view.messages):
            print(f"消息 {i+1}: {msg['sender']} - {msg['content']}")
        print("=======================")
        print(f"消息列表现在包含 {len(self.view.messages)} 条消息")
    
    def scroll_message_to_top(self):
        """将MESSAGE模式的滚动条拉到顶部"""
        if hasattr(self.view, 'message_chat_area') and self.view.message_chat_area is not None:
            self.view.message_chat_area.verticalScrollBar().setValue(0)
            print("将消息滚动条设置到顶部")
    
    def on_mode_changed(self, mode):
        """视图状态变化时的响应"""
        if mode == self.view.LOGO_MODE:
            print("启动截图监控定时器")
            self.screenshot_timer.start(1500)
        elif mode == self.view.MESSAGE_MODE:
            print("当前是MESSAGE模式，确保10秒定时器运行中")
            # 确保消息模式下10秒定时器是运行的
            if not self.view.timer.isActive():
                print("10秒定时器未运行，重新启动")
                self.view.timer.start(10000)
            
            # 停止截图监控定时器
            print("停止截图监控定时器")
            self.screenshot_timer.stop()
        else:
            # CHAT模式
            print("停止截图监控定时器")
            self.screenshot_timer.stop()

class MessageBubble(QFrame):
    """消息气泡组件，用于显示单条消息"""
    def __init__(self, sender, content, parent=None, is_chat_mode=True):
        super().__init__(parent)
        self.sender = sender
        self.content = content
        self.is_chat_mode = is_chat_mode  # 新增：标记是否为CHAT模式
        self.initUI()
        
    def initUI(self):
        # 设置基本样式 - 透明背景，圆角边框
        self.setStyleSheet("background-color: transparent;")
        
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 四周都增加15px的内边距
        layout.setSpacing(10)  # 调整头像和消息间距
        
        # 创建头像标签
        self.avatar_label = QLabel(self)
        self.avatar_label.setFixedSize(60, 60)  # 使用60x60尺寸的头像，符合设计稿
        self.avatar_label.setScaledContents(True)
        
        # 设置圆形头像，添加边框增强圆角效果
        self.avatar_label.setStyleSheet("""
            border-radius: 30px;
            border: 2px solid #D8D8D8;
            background-color: transparent;
            padding: 0px;
            margin: 0px;
        """)
        
        # 根据发送者设置不同的头像
        script_dir = os.path.dirname(os.path.abspath(__file__))
        avatar_path = None
        
        if self.sender == "agent":
            # 尝试加载agent头像
            avatar_paths = [
                os.path.join(script_dir, 'assets', 'front', 'agent.jpg'),
                os.path.join(script_dir, 'assets', 'front', 'logo@1x (1).png'),
                os.path.join(script_dir, 'assets', 'front', 'logo.png')
            ]
            
            # 尝试找到存在的头像文件
            for path in avatar_paths:
                if os.path.exists(path):
                    avatar_path = path
                    break
        else:
            # 尝试加载用户头像
            avatar_paths = [
                os.path.join(script_dir, 'assets', 'front', 'user.jpg'),
                os.path.join(script_dir, 'assets', 'front', 'glasses-line.png')
            ]
            
            # 尝试找到存在的头像文件
            for path in avatar_paths:
                if os.path.exists(path):
                    avatar_path = path
                    break
        
        # 如果没有找到任何头像文件，创建一个默认头像
        if not avatar_path:
            # 创建一个空的头像图片
            pixmap = QPixmap(60, 60)
            pixmap.fill(Qt.transparent)
            
            # 创建画家
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 画圆形背景
            if self.sender == "agent":
                background_color = QColor("#2D7BBA")  # 代理使用蓝色
            else:
                background_color = QColor("#78A679")  # 用户使用绿色
                
            painter.setBrush(QBrush(background_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(2, 2, 56, 56)
            
            # 添加文字标识
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 24, QFont.Bold))
            
            if self.sender == "agent":
                text = "A"
            else:
                text = "U"
                
            # 计算文本位置以居中显示
            text_rect = painter.fontMetrics().boundingRect(text)
            x = (60 - text_rect.width()) / 2
            y = (60 + text_rect.height()) / 2 - 2  # 微调使其在视觉上居中
            
            painter.drawText(int(x), int(y), text)
            painter.end()
            
            # 设置为头像
            self.avatar_label.setPixmap(pixmap)
        else:
            # 加载原始图像
            original_pixmap = QPixmap(avatar_path)
            
            if original_pixmap.isNull():
                # 如果图片加载失败，创建一个替代图片
                pixmap = QPixmap(60, 60)
                pixmap.fill(Qt.transparent)
                
                # 创建画家
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                
                # 画圆形背景
                if self.sender == "agent":
                    background_color = QColor("#2D7BBA")  # 代理使用蓝色
                else:
                    background_color = QColor("#78A679")  # 用户使用绿色
                    
                painter.setBrush(QBrush(background_color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(2, 2, 56, 56)
                
                # 添加文字标识
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont("Arial", 24, QFont.Bold))
                
                if self.sender == "agent":
                    text = "A"
                else:
                    text = "U"
                    
                # 计算文本位置以居中显示
                text_rect = painter.fontMetrics().boundingRect(text)
                x = (60 - text_rect.width()) / 2
                y = (60 + text_rect.height()) / 2 - 2  # 微调使其在视觉上居中
                
                painter.drawText(int(x), int(y), text)
                painter.end()
                
                # 设置为头像
                self.avatar_label.setPixmap(pixmap)
            else:
                # 创建一个圆形遮罩
                target_pixmap = QPixmap(60, 60)
                target_pixmap.fill(Qt.transparent)  # 填充透明背景
                
                # 创建画家
                painter = QPainter(target_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿
                
                # 创建圆形路径
                path = QPainterPath()
                path.addEllipse(2, 2, 56, 56)  # 保留2px边框宽度的空间
                painter.setClipPath(path)
                
                # 缩放原始图像并画在目标上
                scaled_pixmap = original_pixmap.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(2, 2, scaled_pixmap)
                
                # 结束绘制
                painter.end()
                
                # 设置圆形图像
                self.avatar_label.setPixmap(target_pixmap)
        
        # 创建消息框架 - 白色背景
        message_frame = QFrame(self)
        message_frame.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 20px;
            border: none;
            outline: none;
        """)
        
        # 消息框架使用垂直布局
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(0, 0, 0, 0)  # 减少顶部内边距，使文本更靠近顶部
        message_layout.setAlignment(Qt.AlignTop)  # 设置整体布局顶部对齐
        
        # 创建内容容器（不再用QScrollArea）
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent; border: none;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加消息内容标签
        content_label = QLabel()
        content_label.setText(self.content)
        content_label.setWordWrap(True)  # 启用自动换行
        content_label.setMinimumWidth(520)  # 设置最小宽度，防止过早换行
        content_label.setTextFormat(Qt.RichText)  # 强制使用富文本格式
        content_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)  # 允许选择和点击链接
        content_label.setStyleSheet("""
            color: #343434;
            font-family: 'PingFang SC';
            font-size: 26px;
            font-weight: 500;
            line-height: 36px;  /* 增加行高，使文本更加舒适 */
            letter-spacing: 0px;  /* 设置固定字间距 */
            background-color: transparent;
            padding: 5px 10px;  /* 增加水平内边距 */
            margin: 0px;
            border: none;
        """)
        
        # 设置大小策略，固定宽度，确保不会过早换行
        content_label.setMaximumWidth(520)
        content_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        
        # 添加标签到内容布局
        content_layout.addWidget(content_label)
        
        # 检查是否需要插入图片
        if ("目录" in self.content) and ("图像" in self.content):
            test_img_path = os.path.join(script_dir, 'assets/demo_pic', 'test.jpg')
            if os.path.exists(test_img_path):
                # 加载图片
                img_pixmap = QPixmap(test_img_path)
                # 计算目标宽度和等比例高度
                target_width = 520
                if not img_pixmap.isNull():
                    aspect_ratio = img_pixmap.height() / img_pixmap.width()
                    target_height = int(target_width * aspect_ratio)
                    # 缩放图片
                    scaled_img = img_pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    # 创建带圆角遮罩的图片
                    rounded_img = QPixmap(target_width, target_height)
                    rounded_img.fill(Qt.transparent)
                    painter = QPainter(rounded_img)
                    painter.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    path.addRoundedRect(0, 0, target_width, target_height, 15, 15)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, scaled_img)
                    painter.end()
                    # 创建图片标签
                    img_label = QLabel()
                    img_label.setPixmap(rounded_img)
                    img_label.setFixedSize(target_width, target_height)
                    img_label.setScaledContents(True)
                    # 添加到内容布局
                    content_layout.addWidget(img_label)
            else:
                # 如果图片不存在，创建一个占位图像
                placeholder_pixmap = QPixmap(520, 300)  # 创建一个适当尺寸的占位图
                placeholder_pixmap.fill(QColor("#F0F0F0"))  # 浅灰色背景
                
                # 创建画家
                painter = QPainter(placeholder_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                
                # 添加文字说明
                painter.setPen(QColor("#666666"))
                painter.setFont(QFont("Arial", 14))
                painter.drawText(placeholder_pixmap.rect(), Qt.AlignCenter, "示例图片 (无法加载)")
                
                # 画个边框
                painter.setPen(QPen(QColor("#CCCCCC"), 2))
                painter.drawRoundedRect(1, 1, 518, 298, 15, 15)
                painter.end()
                
                # 创建图片标签
                img_label = QLabel()
                img_label.setPixmap(placeholder_pixmap)
                img_label.setFixedSize(520, 300)
                
                # 添加到内容布局
                content_layout.addWidget(img_label)
        
                # --- 增加底部按钮 ---
                btn_layout = QHBoxLayout()
                btn_layout.setContentsMargins(0, 15, 0, 0)
                btn_layout.setSpacing(20)

                # 第一个按钮：主色
                btn1 = QPushButton("打开目录")
                btn1.setFixedSize(155, 40)
                btn1.setStyleSheet("""
                    QPushButton {
                        background-color: #2D7BBA;
                        color: #fff;
                        border: none;
                        border-radius: 20px;
                        font-size: 18px;
                        font-family: 'PingFang SC';
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #226099;
                    }
                """)
                # 添加点击事件，打开目录
                def open_dir():
                    import os, sys, subprocess
                    # 这里以当前工作目录为例，你可以替换为你想要的目录
                    dir_path = os.getcwd()+"/assets/demo_pic"
                    if sys.platform.startswith('win'):
                        os.startfile(dir_path)
                    elif sys.platform.startswith('darwin'):
                        subprocess.Popen(['open', dir_path])
                    else:
                        subprocess.Popen(['xdg-open', dir_path])
                btn1.clicked.connect(open_dir)

                # 第二个按钮：白底蓝字
                btn2 = QPushButton("编写回复邮件")
                btn2.setFixedSize(155, 40)
                btn2.setStyleSheet("""
                    QPushButton {
                        background-color: #2D7BBA;
                        color: #fff;
                        border: none;
                        border-radius: 20px;
                        font-size: 18px;
                        font-family: 'PingFang SC';
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #226099;
                    }
                """)
                # 第二个按钮：白底蓝字
                btn3 = QPushButton("打包目录文件")
                btn3.setFixedSize(155, 40)
                btn3.setStyleSheet("""
                    QPushButton {
                        background-color: #2D7BBA;
                        color: #fff;
                        border: none;
                        border-radius: 20px;
                        font-size: 18px;
                        font-family: 'PingFang SC';
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #226099;
                    }
                """)

                btn_layout.addWidget(btn1)
                btn_layout.addWidget(btn2)
                btn_layout.addWidget(btn3)
                btn_layout.addStretch(1)

                content_layout.addLayout(btn_layout)
        if ("攻略" in self.content) :
            gif_path = os.path.join(script_dir, 'assets/demo_pic', 'guangzhi.gif')
            if os.path.exists(gif_path):
                movie = QMovie(gif_path)
                movie.setScaledSize(QSize(520, 292))  # 你可以根据实际gif比例调整高度
                img_label = QLabel()
                img_label.setMovie(movie)
                img_label.setFixedSize(520, 292)  # 宽高和setScaledSize一致
                img_label.setScaledContents(True)
                movie.start()
                # 创建圆角遮罩
                path = QPainterPath()
                path.addRoundedRect(0, 0, 520, 292, 20, 20)  # 20为圆角半径
                region = QRegion(path.toFillPolygon().toPolygon())
                img_label.setMask(region)
                content_layout.addWidget(img_label)

        if ("攻略123" in self.content) :
            test_img_path = os.path.join(script_dir, 'assets/demo_pic', 'guangzhi.jpg')
            if os.path.exists(test_img_path):
                # 加载图片
                img_pixmap = QPixmap(test_img_path)
                # 计算目标宽度和等比例高度
                target_width = 520
                if not img_pixmap.isNull():
                    aspect_ratio = img_pixmap.height() / img_pixmap.width()
                    target_height = int(target_width * aspect_ratio)
                    # 缩放图片
                    scaled_img = img_pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    # 创建带圆角遮罩的图片
                    rounded_img = QPixmap(target_width, target_height)
                    rounded_img.fill(Qt.transparent)
                    painter = QPainter(rounded_img)
                    painter.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    path.addRoundedRect(0, 0, target_width, target_height, 15, 15)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, scaled_img)
                    painter.end()
                    # 创建图片标签
                    img_label = QLabel()
                    img_label.setPixmap(rounded_img)
                    img_label.setFixedSize(target_width, target_height)
                    img_label.setScaledContents(True)
                    # 添加到内容布局
                    content_layout.addWidget(img_label)

            if 0:
                if 1:
        
                    # --- 增加底部按钮 ---
                    btn_layout = QVBoxLayout()
                    btn_layout.setContentsMargins(0, 0, 0, 0)
                    btn_layout.setSpacing(20)

                    # 第一个按钮：主色
                    btn1 = QPushButton("虎先锋技能拆解和打法思路分享 ")
                    btn1.setFixedSize(520, 45)
                    btn1.setStyleSheet("""
                        QPushButton {
                            background-color: #2D7BBA;
                            color: #fff;
                            border: none;
                            border-radius: 20px;
                            font-size: 18px;
                            font-family: 'PingFang SC';
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background-color: #226099;
                        }
                    """)
                    # 添加点击事件，打开浏览器链接
                    def open_link():
                        import webbrowser
                        webbrowser.open('https://www.gamersky.com/handbook/202409/1809823.shtml')
                    btn1.clicked.connect(open_link)

                    # 第二个按钮：白底蓝字
                    btn2 = QPushButton("虎先锋怎么打？一周目手残党也能抄的打法")
                    btn2.setFixedSize(520, 45)
                    btn2.setStyleSheet("""
                        QPushButton {
                            background-color: #2D7BBA;
                            color: #fff;
                            border: none;
                            border-radius: 20px;
                            font-size: 18px;
                            font-family: 'PingFang SC';
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background-color: #226099;
                        }
                    """)
                    # 第二个按钮：白底蓝字
                    btn3 = QPushButton("黑神话悟空虎先锋打法攻略")
                    btn3.setFixedSize(520, 45)
                    btn3.setStyleSheet("""
                        QPushButton {
                            background-color: #2D7BBA;
                            color: #fff;
                            border: none;
                            border-radius: 20px;
                            font-size: 18px;
                            font-family: 'PingFang SC';
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background-color: #226099;
                        }
                    """)

                    btn_layout.addWidget(btn1)
                    btn_layout.addWidget(btn2)
                    btn_layout.addWidget(btn3)
                    btn_layout.addStretch(1)

                    content_layout.addLayout(btn_layout)                   
        # 将内容容器添加到消息布局
        message_layout.addWidget(content_widget)
        
        # 根据发送者设置布局顺序，调整布局让消息靠近两侧
        if self.sender == "user":
            # 用户消息也靠左对齐
            layout.addWidget(self.avatar_label, 0, Qt.AlignLeft | Qt.AlignTop)
            layout.addWidget(message_frame, 0, Qt.AlignTop)  # 改为顶部对齐
        else:
            layout.addWidget(self.avatar_label, 0, Qt.AlignLeft | Qt.AlignTop)  # 改为顶部对齐
            layout.addWidget(message_frame, 0, Qt.AlignTop)  # 改为顶部对齐
    


class ProgressCircle(QWidget):
    """圆形进度条，显示倒计时"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(36, 36)
        self.setMaximumSize(36, 36)
        self.progress = 100  # 初始进度为100%
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        
    def start_countdown(self, duration=10000):
        """启动倒计时，默认10秒"""
        self.progress = 100
        self.step = 100 / (duration / 100)  # 每100毫秒的进度减少量
        self.timer.start(100)  # 每100毫秒更新一次
        
    def stop_countdown(self):
        """停止倒计时"""
        self.timer.stop()
        
    def update_progress(self):
        """更新进度"""
        self.progress -= self.step
        if self.progress <= 0:
            self.progress = 0
            self.timer.stop()
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        """绘制圆形进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制外圆背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(200, 200, 200, 100)))
        painter.drawEllipse(3, 3, 30, 30)
        
        # 计算角度
        angle = int(360 * self.progress / 100)
        
        # 绘制进度圆弧
        painter.setPen(QPen(QColor(70, 130, 180), 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(3, 3, 30, 30, 90 * 16, -angle * 16)  # 从顶部开始，逆时针绘制


class ChatRequestThread(QThread):
    """处理聊天请求的线程"""
    response_received = pyqtSignal(str)  # 接收到响应时发出信号
    error_occurred = pyqtSignal(str)     # 发生错误时发出信号
    
    def __init__(self, user_message):
        super().__init__()
        self.user_message = user_message
        # 设置API的URL和key
        self.api_key = "sk-ef4b56e3bc9c4693b596415dd364af56"
        # self.api_base = "http://10.8.30.136:49160/v1"  # 正确的API地址
        self.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 正确的API地址

    def run(self):
        try:
            # 打印发送的消息（用于调试）
            print(f"发送到后端的消息: {self.user_message}")
            
            # 创建OpenAI客户端
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
            )
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 发送请求
            try:
                chat_response = client.chat.completions.create(
                    model="qwen3-14b",  # 可以根据实际情况调整模型
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": [
                            {"type": "text", "text": self.user_message}
                        ]}
                    ],
                    stream=True,
                    extra_body={"enable_thinking": False},
                    stream_options={"include_usage": True}
                )
                
                # 计算响应时间
                elapsed_time = (datetime.now() - start_time).total_seconds()
                print(f"请求用时: {elapsed_time:.2f} 秒")
                import json
                res = ""
                for chunk in chat_response:
                    # print(chunk.model_dump_json())
                    # 使用json.loads()方法将字符串转换为字典
                    dict_obj = json.loads(chunk.model_dump_json())
                    # print(dict_obj)
                    # print(
                    a  = dict_obj["choices"]
                    
                    if len(a):
                        res+= a[0]["delta"]["content"]

                # 提取响应文本
                response_text = res #chat_response.choices[0].message.content
                print(f"收到回复: {response_text}")
                
                # 发出信号，传递响应
                self.response_received.emit(response_text)
                
            except Exception as e:
                print(f"API请求错误: {e}")
                # 如果API请求失败，使用备用响应
                fallback_message = f"抱歉，我暂时无法连接到服务器。错误信息: {str(e)}"
                self.error_occurred.emit(fallback_message)
                
        except Exception as e:
            print(f"线程执行错误: {e}")
            self.error_occurred.emit(f"处理请求时发生错误: {str(e)}")


class FreeYouApp(QMainWindow):
    # 定义模式常量
    LOGO_MODE = 0
    MESSAGE_MODE = 1
    CHAT_MODE = 2
    
    # 定义状态变化信号
    mode_changed = pyqtSignal(int)
    # 添加关闭前信号
    aboutToClose = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.dragging = False
        self.current_mode = self.CHAT_MODE  # 初始为chat模式
        self.timer = QTimer(self)  # 创建定时器
        self.timer.timeout.connect(self.enterLogoMode)  # 连接定时器到logo模式切换函数
        self.animation_duration = 300  # 动画持续时间（毫秒）
        
        # 添加图标缩放因子
        self.icon_scale_factor = 1.2
        
        # 初始化消息列表
        self.messages = []
        # 添加一条初始消息
        self.messages.append({"sender": "agent", "content": "Hello! How can I assist you today? 😊"})
        
        # 添加自动关闭定时器 (5分钟 = 300000毫秒)
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.timeout.connect(self.closeApplication)
        self.auto_close_timer.setSingleShot(True)  # 只触发一次
        self.auto_close_timer.start(300000)  # 5分钟后自动关闭
        
        # 添加剩余时间显示
        self.time_remaining = 300  # 初始300秒
        self.time_display_timer = QTimer(self)
        self.time_display_timer.timeout.connect(self.updateTimeDisplay)
        self.time_display_timer.start(1000)  # 每秒更新一次
        
        self.initUI()
    
    def closeApplication(self):
        """自动关闭应用程序"""
        print("应用程序已运行5分钟，正在自动关闭...")
        QApplication.quit()
    
    def updateTimeDisplay(self):
        """更新剩余时间显示"""
        self.time_remaining -= 1
        if self.time_remaining <= 0:
            self.time_display_timer.stop()
        
        # 只在控制台显示剩余时间，每30秒显示一次
        if self.time_remaining % 30 == 0:
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            print(f"程序将在 {minutes}分{seconds}秒 后自动关闭")
    
    def closeEvent(self, event):
        """重写关闭事件，确保程序可以正常关闭"""
        # 发出关闭前信号
        self.aboutToClose.emit()
        
        # 停止所有正在运行的线程和定时器
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        
        if hasattr(self, 'auto_close_timer') and self.auto_close_timer.isActive():
            self.auto_close_timer.stop()
            
        if hasattr(self, 'time_display_timer') and self.time_display_timer.isActive():
            self.time_display_timer.stop()
        
        # 关闭所有可能在运行的线程
        for thread in QThreadPool.globalInstance().children():
            if isinstance(thread, QThread) and thread.isRunning():
                thread.quit()
                thread.wait()
        
        # 接受关闭事件
        event.accept()
    
    def initUI(self):
        # 设置主窗口
        self.setWindowTitle('FreeYou')
        self.setFixedSize(788, 980)  # 向外扩展30px padding (708+80, 900+80)
        
        # 创建边距框架 - 用于实现40px的边距
        self.padding_frame = QFrame(self)
        self.padding_frame.setGeometry(0, 0, 788, 980)
        self.padding_frame.setStyleSheet("background-color: transparent;")
        
        # 主框架 - 内容区域保持原大小
        self.main_frame = QFrame(self.padding_frame)
        self.main_frame.setGeometry(0, 0, 788, 980)  # 位于padding_frame内部，有40px边距
        self.main_frame.setStyleSheet("background-color: transparent; border-radius: 21px;")
        
        # 添加背景层 - 仅用于显示背景色，位于main_frame中
        self.bg_frame = QFrame(self.main_frame)
        self.bg_frame.setGeometry(40, 40, 708, 900)  # 保持不变，设计稿显示应该是这个尺寸
        
        # 根据当前模式设置圆角
        if self.current_mode == self.CHAT_MODE:
            self.bg_frame.setStyleSheet("background-color: #F7F7F7; border-radius: 21px;")  # CHAT模式为21px圆角
        else:
            self.bg_frame.setStyleSheet("background-color: #F7F7F7; border-radius: 38px;")  # MESSAGE模式为38px圆角
            
        self.bg_frame.lower()  # 确保背景在最底层
        
        # 初始化时就应用阴影效果
        self.apply_shadow_to_bg_frame()
        
        # 创建界面元素
        self.createUIElements()
        
        # 设置窗口为圆角
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 记录logo的固定位置
        self.logo_fixed_position = QPoint(20, 20)
        
        self.setCentralWidget(self.padding_frame)
        self.show()
    
    def createUIElements(self):
        # LOGO图像
        self.logo_container = ShadowFrame(self.main_frame, radius=24, shadow_blur=0, shadow_color=QColor("#273246"))
        self.logo_container.setGeometry(20+40, 20+40, 60, 60)  # 将logo尺寸从128x128改为60x60
        self.logo_container.setStyleSheet("background-color: transparent;")
        
        self.logo_label = QLabel(self.logo_container)
        self.logo_label.setGeometry(0, 0, 60, 60)  # 将logo标签尺寸也改为60x60
        
        # 设置LOGO图像 - MESSAGE模式使用原有logo
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, 'assets', 'front', 'logo.png')
        
        # 检查logo文件是否存在，如果不存在则创建一个默认logo
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            if logo_pixmap.isNull():
                self.createDefaultLogo()
            else:
                self.logo_label.setPixmap(logo_pixmap)
                self.logo_label.setScaledContents(True)
        else:
            self.createDefaultLogo()
            
        self.logo_label.hide()
        
        # 右侧控制面板 - 使用QFrame替代ShadowFrame，使用新的边框样式 - 这是chat模式使用的水平面板
        self.control_panel = QFrame(self.bg_frame)
        self.control_panel.setGeometry(556, 33, 139, 51)  # 按照最新设计稿尺寸和位置
        self.control_panel.setStyleSheet("""
            background-color: #D8D8D8;
            border: 3px solid #A4A4A4;
            border-radius: 24px;
        """)
        
        # 添加控制按钮 - 折叠按钮
        self.collapse_btn = QPushButton(self.control_panel)
        self.collapse_btn.setGeometry(80, 8, 36, 36)  # 根据设计稿调整位置和大小
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(176, 193, 222, 0.5);
                border-radius: 9px;
            }
        """)
        
        # 尝试加载折叠图标
        collapse_path = os.path.join(script_dir, 'assets', 'front', 'collapse-diagonal-2-line.png')
        if os.path.exists(collapse_path):
            collapse_pixmap = QPixmap(collapse_path)
            if not collapse_pixmap.isNull():
                collapse_icon = QIcon(collapse_pixmap)
                self.collapse_btn.setIcon(collapse_icon)
                # 应用图标缩放因子
                collapse_size = int(26 * self.icon_scale_factor)
                self.collapse_btn.setIconSize(QSize(collapse_size, collapse_size))
            else:
                self.createDefaultCollapseButton()
        else:
            self.createDefaultCollapseButton()
            
        self.collapse_btn.clicked.connect(self.toggleExpandCollapse)
        
        # 添加控制按钮 - 设置按钮
        self.settings_btn = QPushButton(self.control_panel)
        self.settings_btn.setGeometry(24, 8, 36, 36)  # 根据设计稿调整位置和大小
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(176, 193, 222, 0.5);
                border-radius: 9px;
            }
        """)
        
        # 尝试加载设置图标
        settings_path = os.path.join(script_dir, 'assets', 'front', 'settings-line.png')
        if os.path.exists(settings_path):
            settings_pixmap = QPixmap(settings_path)
            if not settings_pixmap.isNull():
                settings_icon = QIcon(settings_pixmap)
                self.settings_btn.setIcon(settings_icon)
                # 应用图标缩放因子
                settings_size = int(26 * self.icon_scale_factor)
                self.settings_btn.setIconSize(QSize(settings_size, settings_size))
            else:
                self.createDefaultSettingsButton()
        else:
            self.createDefaultSettingsButton()
        
        # 创建竖直控制面板 - 仅用于message模式
        self.vertical_control_panel = QFrame(self.bg_frame)
        self.vertical_control_panel.setGeometry(620, 24, 51, 120)  # 根据MasterGo设计调整位置和尺寸
        self.vertical_control_panel.setStyleSheet("""
            background-color: transparent;
            border: 3px solid #2D7BBA;
            border-radius: 18px;
        """)
        
        # 为垂直控制面板添加阴影效果
        # shadow_color = QColor(0, 0, 0, 76)
        shadow_color = QColor(45, 123, 186, 99)
        shadow_offset_y = 4
        shadow_blur_radius = 10
        
        v_panel_shadow = QGraphicsDropShadowEffect()
        v_panel_shadow.setBlurRadius(shadow_blur_radius)
        v_panel_shadow.setColor(shadow_color)
        v_panel_shadow.setOffset(0, shadow_offset_y)
        self.vertical_control_panel.setGraphicsEffect(v_panel_shadow)
        
        # 竖直控制面板布局
        v_panel_layout = QVBoxLayout(self.vertical_control_panel)
        v_panel_layout.setContentsMargins(5, 10, 7, 10)  # 根据设计调整内边距
        v_panel_layout.setSpacing(15)  # 根据设计调整按钮间距
        
        # 新增：进度圆圈用于替代设置按钮
        self.progress_circle = ProgressCircle()
        
        # 关闭按钮 - 添加在顶部
        v_close_btn = QPushButton()
        v_close_btn.setFixedSize(36, 36)
        v_close_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4D4F;
                border: none;
                border-radius: 18px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF7875;
            }
        """)
        v_close_btn.setText("X")
        v_close_btn.clicked.connect(self.closeApplication)
        
        # 折叠按钮 - 竖直面板
        v_collapse_btn = QPushButton()
        v_collapse_btn.setFixedSize(36, 36)
        v_collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(176, 193, 222, 0.5);
                border-radius: 9px;
            }
        """)

        # 尝试加载或创建图标
        collapse_path = os.path.join(script_dir, 'assets', 'front', 'collapse-diagonal-2-line.png')
        if os.path.exists(collapse_path):
            collapse_pixmap = QPixmap(collapse_path)
            if not collapse_pixmap.isNull():
                collapse_icon = QIcon(collapse_pixmap)
                v_collapse_btn.setIcon(collapse_icon)
            else:
                # 创建默认折叠图标
                self.createDefaultCollapseIcon(v_collapse_btn)
        else:
            # 创建默认折叠图标
            self.createDefaultCollapseIcon(v_collapse_btn)
            
        # 应用图标缩放因子
        v_icon_size = int(26 * self.icon_scale_factor)
        v_collapse_btn.setIconSize(QSize(v_icon_size, v_icon_size))  # 使用缩放因子
        v_collapse_btn.clicked.connect(self.toggleExpandCollapse)
        
        # 添加按钮到垂直控制面板
        v_panel_layout.addWidget(v_close_btn, 0, Qt.AlignCenter)  # 关闭按钮放在顶部
        v_panel_layout.addWidget(self.progress_circle, 0, Qt.AlignCenter)
        v_panel_layout.addWidget(v_collapse_btn, 0, Qt.AlignCenter)
        
        # 初始隐藏垂直控制面板
        self.vertical_control_panel.hide()
        
        # 创建聊天区域下方的矩形容器 - 对应MasterGo设计稿中的"容器 39"
        self.bottom_container = QFrame(self.bg_frame)
        self.bottom_container.setGeometry(20, 668, 668, 215)  # 根据设计稿调整位置和大小
        self.bottom_container.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 21px;
            border: none;
        """)
        
        # 为底部容器添加阴影效果
        bottom_container_shadow = QGraphicsDropShadowEffect()
        bottom_container_shadow.setBlurRadius(6)  # 模糊度为6
        bottom_container_shadow.setColor(QColor(39, 72, 129, 77))  # #274881 透明度30%
        bottom_container_shadow.setOffset(0, 0)  # X=0, Y=0 不偏移
        # self.bottom_container.setGraphicsEffect(bottom_container_shadow)
        
        # 底部发送消息栏 - 只在展开状态显示 - 使用新的边框样式
        self.message_bar = QFrame(self.bottom_container)
        self.message_bar.setGeometry(26, 31, 615, 161)  # 根据设计稿调整位置和大小
        self.message_bar.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 21px;
            border: 2px solid #D8D8D8;
        """)
        
        # 为消息栏添加阴影效果
        shadow_color = QColor(39, 72, 129, 45)  # 约等于rgba(0, 0, 0, 0.3)
        shadow_offset_y = 0
        shadow_blur_radius = 30  # 根据设计稿修改为10px
        
        message_bar_shadow = QGraphicsDropShadowEffect()
        message_bar_shadow.setBlurRadius(shadow_blur_radius)
        message_bar_shadow.setColor(shadow_color)
        message_bar_shadow.setOffset(0, shadow_offset_y)
        # self.message_bar.setGraphicsEffect(message_bar_shadow)
        self.message_bar.setGraphicsEffect(message_bar_shadow)
        
        # 消息栏布局 - 移除布局管理，改用绝对位置
        # msg_layout = QHBoxLayout(self.message_bar)
        # msg_layout.setContentsMargins(15, 5, 15, 5)
        # msg_layout.setSpacing(15)  # 调整按钮间距

        # 附件按钮
        attachment_btn = QPushButton(self.message_bar)
        attachment_btn.setGeometry(20, 110, 36, 36)  # 根据设计稿调整位置
        attachment_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(39, 72, 129, 0.1);
                border-radius: 9px;
            }
        """)

        attachment_path = os.path.join(script_dir, 'assets', 'front', 'attachment-2.png')
        attachment_pixmap = QPixmap(attachment_path)
        attachment_icon = QIcon(attachment_pixmap)
        attachment_btn.setIcon(attachment_icon)
        # 应用缩放因子
        attachment_width = int(26 * self.icon_scale_factor)
        attachment_height = int(28 * self.icon_scale_factor)
        attachment_btn.setIconSize(QSize(attachment_width, attachment_height))  # 使用缩放因子

        # 输入框 - 使用绝对位置
        self.input_field = FocusShadowLineEdit(self.message_bar, message_bar=self.message_bar)
        self.input_field.setGeometry(20, 15, 580, 45)  # 根据设计稿调整位置和大小
        self.input_field.setPlaceholderText("发送消息...")
        self.input_field.setStyleSheet("""
            border: none;
            font-family: 'PingFang SC';
            font-size: 26px;
            font-weight: 6000;
            line-height: 30px;
            letter-spacing: 0.5px;
            color: #274881;
            background-color: transparent;
""")

        # 连接回车键发送消息
        self.input_field.returnPressed.connect(self.sendMessage)

        # 云按钮
        cloud_btn = QPushButton(self.message_bar)
        cloud_btn.setGeometry(520, 110, 36, 36)  # 根据设计稿调整位置
        cloud_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(39, 72, 129, 0.1);
                border-radius: 9px;
            }
        """)

        cloud_path = os.path.join(script_dir, 'assets', 'front', 'cloud-line.png')
        cloud_pixmap = QPixmap(cloud_path)
        cloud_icon = QIcon(cloud_pixmap)
        cloud_btn.setIcon(cloud_icon)
        # 应用缩放因子
        cloud_width = int(33 * self.icon_scale_factor)
        cloud_height = int(28 * self.icon_scale_factor)
        cloud_btn.setIconSize(QSize(cloud_width, cloud_height))  # 使用缩放因子

        # 发送按钮
        send_btn = QPushButton(self.message_bar)
        send_btn.setGeometry(565, 110, 36, 36)  # 根据设计稿调整位置
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(39, 72, 129, 0.1);
                border-radius: 9px;
            }
        """)

        send_path = os.path.join(script_dir, 'assets', 'front', 'send-plane-line.png')
        send_pixmap = QPixmap(send_path)
        send_icon = QIcon(send_pixmap)
        send_btn.setIcon(send_icon)
        # 应用缩放因子
        send_width = int(30 * self.icon_scale_factor)
        send_height = int(30 * self.icon_scale_factor)
        send_btn.setIconSize(QSize(send_width, send_height))  # 使用缩放因子

        # 连接发送按钮点击事件
        send_btn.clicked.connect(self.sendMessage)

        # 不再需要添加到布局
        # msg_layout.addWidget(attachment_btn, 0, Qt.AlignVCenter)
        # msg_layout.addWidget(self.input_field, 1)
        # msg_layout.addWidget(cloud_btn, 0, Qt.AlignVCenter)
        # msg_layout.addWidget(send_btn, 0, Qt.AlignVCenter)
        
        # 初始化时隐藏消息栏，只在Chat模式下显示
        self.bottom_container.hide()
        self.message_bar.hide()
        
        # 初始化消息列表
        if not hasattr(self, 'messages'):
            self.messages = []
            # 添加一条初始消息
            self.messages.append({"sender": "agent", "content": "Hello! How can I assist you today? 😊"})
        
        # 根据当前模式设置初始可见性
        if self.current_mode == self.CHAT_MODE:
            # 如果初始为CHAT模式，设置并显示CHAT界面
            self.setup_chat_area()
            self.setupChatHeader()
            self.bottom_container.show()
            self.message_bar.show()
        elif self.current_mode == self.MESSAGE_MODE:
            # 创建message模式的聊天区域
            self.message_chat_area = QScrollArea(self.bg_frame)
            self.message_chat_area.setGeometry(170, 31, 427, 105)  # 调整高度为105px
            self.message_chat_area.setStyleSheet("""
                background-color: transparent;
                border: none;
            """)
            self.message_chat_area.setWidgetResizable(True)
            self.message_chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.message_chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # 创建聊天内容容器
            self.message_chat_container = QWidget()
            self.message_chat_container.setStyleSheet("""
                background-color: transparent;
                padding: 5px;
            """)
            
            # 设置聊天容器的布局
            self.message_chat_layout = QVBoxLayout(self.message_chat_container)
            self.message_chat_layout.setContentsMargins(15, 15, 15, 15)  # 四周都增加15px内边距
            self.message_chat_layout.setSpacing(10)
            self.message_chat_layout.setAlignment(Qt.AlignLeft)  # 更改为左对齐
            
            # 添加弹性空间，使最新消息始终在底部显示
            self.message_chat_layout.addStretch(1)
            
            # 将容器设置为滚动区域的部件
            self.message_chat_area.setWidget(self.message_chat_container)
            
            # 添加简化版的消息
            self.addSimplifiedMessage()
            
            # 隐藏CHAT模式元素
            if hasattr(self, 'header_frame'):
                self.header_frame.hide()
            if hasattr(self, 'header_divider'):
                self.header_divider.hide()
            self.message_bar.hide()
    
    def toggleExpandCollapse(self):
        if self.current_mode == self.LOGO_MODE:
            # 从logo模式恢复到message模式
            self.exitLogoMode()
            return
            
        if self.current_mode == self.CHAT_MODE:
            # 切换到简约模式（message模式）
            # 隐藏chat模式特有元素
            if hasattr(self, 'header_frame'):
                self.header_frame.hide()
            if hasattr(self, 'header_divider'):
                self.header_divider.hide()
            
            # 隐藏CHAT模式头部元素
            if hasattr(self, 'chat_title_label'):
                self.chat_title_label.hide()
            if hasattr(self, 'chat_logo'):
                self.chat_logo.hide()
            if hasattr(self, 'chat_collapse_btn'):
                self.chat_collapse_btn.hide()
            if hasattr(self, 'chat_settings_btn'):
                self.chat_settings_btn.hide()
            
            # 隐藏当前聊天区域
            self.chat_area.hide()
            
            # 创建动画组
            self.animation_group = QParallelAnimationGroup(self)
            
            # 窗口大小动画
            self.resize_animation = QPropertyAnimation(self, b"size")
            self.resize_animation.setDuration(self.animation_duration)
            self.resize_animation.setStartValue(self.size())
            self.resize_animation.setEndValue(QSize(728, 191))  # 708+20, 171+20 向外扩展10px
            self.resize_animation.setEasingCurve(QEasingCurve.OutQuint)  # 使用更平滑的缓动曲线
            
            # padding框架大小动画
            self.padding_resize_animation = QPropertyAnimation(self.padding_frame, b"geometry")
            self.padding_resize_animation.setDuration(self.animation_duration)
            self.padding_resize_animation.setStartValue(self.padding_frame.geometry())
            self.padding_resize_animation.setEndValue(QRect(0, 0, 788, 171+80))
            self.padding_resize_animation.setEasingCurve(QEasingCurve.OutQuint)  # 使用更平滑的缓动曲线
            
            # 主框架大小动画
            self.frame_resize_animation = QPropertyAnimation(self.main_frame, b"geometry")
            self.frame_resize_animation.setDuration(self.animation_duration)
            self.frame_resize_animation.setStartValue(self.main_frame.geometry())
            self.frame_resize_animation.setEndValue(QRect(0, 0, 788, 171+80))
            self.frame_resize_animation.setEasingCurve(QEasingCurve.OutQuint)  # 使用更平滑的缓动曲线
            
            # 背景框架大小动画
            self.bg_resize_animation = QPropertyAnimation(self.bg_frame, b"geometry")
            self.bg_resize_animation.setDuration(self.animation_duration)
            self.bg_resize_animation.setStartValue(self.bg_frame.geometry())
            self.bg_resize_animation.setEndValue(QRect(40, 40, 708, 171))
            self.bg_resize_animation.setEasingCurve(QEasingCurve.OutQuint)  # 使用更平滑的缓动曲线
            
            # 添加动画到组
            self.animation_group.addAnimation(self.resize_animation)
            self.animation_group.addAnimation(self.padding_resize_animation)
            self.animation_group.addAnimation(self.frame_resize_animation)
            self.animation_group.addAnimation(self.bg_resize_animation)
            
            # 设置动画完成后的操作
            self.animation_group.finished.connect(lambda: self._after_collapse_animation())
            
            # 启动动画
            self.animation_group.start()
            
            # 立即隐藏一些元素
            self.message_bar.hide()
            
            self.current_mode = self.MESSAGE_MODE
            
            # MESSAGE模式下设置背景圆角为38px
            self.bg_frame.setStyleSheet("background-color: #F7F7F7; border-radius: 38px;")
            
            # 发出状态变化信号
            self.mode_changed.emit(self.MESSAGE_MODE)
        elif self.current_mode == self.MESSAGE_MODE:
            # 切换到完整模式（chat模式）
            # 停止定时器和进度圈
            self.timer.stop()
            self.progress_circle.stop_countdown()
            
            # 隐藏当前元素
            self.logo_container.hide()
            
            # 将logo尺寸重置为CHAT模式下的60px，以便下次进入CHAT模式
            self.setLogoSize(60)
            
            self.vertical_control_panel.hide()
            
            # 隐藏message聊天区域
            if hasattr(self, 'message_chat_area'):
                self.message_chat_area.hide()
            
            # 创建动画组
            self.animation_group = QParallelAnimationGroup(self)
            
            # 窗口大小动画
            self.resize_animation = QPropertyAnimation(self, b"size")
            self.resize_animation.setDuration(self.animation_duration)
            self.resize_animation.setStartValue(self.size())
            self.resize_animation.setEndValue(QSize(788, 980))  # 708+80, 900+80
            self.resize_animation.setEasingCurve(QEasingCurve.OutQuint)  # 使用更平滑的缓动曲线
            
            # padding框架大小动画
            self.padding_resize_animation = QPropertyAnimation(self.padding_frame, b"geometry")
            self.padding_resize_animation.setDuration(self.animation_duration)
            self.padding_resize_animation.setStartValue(self.padding_frame.geometry())
            self.padding_resize_animation.setEndValue(QRect(0, 0, 788, 980))
            self.padding_resize_animation.setEasingCurve(QEasingCurve.OutQuint)  # 使用更平滑的缓动曲线
            
            # 主框架动画
            self.frame_anim = QPropertyAnimation(self.main_frame, b"geometry")
            self.frame_anim.setDuration(self.animation_duration)
            self.frame_anim.setStartValue(self.main_frame.geometry())
            self.frame_anim.setEndValue(QRect(0, 0, 788, 980))
            self.frame_anim.setEasingCurve(QEasingCurve.OutQuint)
            
            # 背景框架动画
            self.bg_frame_anim = QPropertyAnimation(self.bg_frame, b"geometry")
            self.bg_frame_anim.setDuration(self.animation_duration)
            self.bg_frame_anim.setStartValue(self.bg_frame.geometry())
            self.bg_frame_anim.setEndValue(QRect(40, 40, 708, 900))
            self.bg_frame_anim.setEasingCurve(QEasingCurve.OutQuint)
            
            # 添加动画到组
            self.animation_group.addAnimation(self.resize_animation)
            self.animation_group.addAnimation(self.padding_resize_animation)
            self.animation_group.addAnimation(self.frame_anim)
            self.animation_group.addAnimation(self.bg_frame_anim)
            
            # 设置动画完成后的操作
            self.animation_group.finished.connect(lambda: self._after_expand_animation())
            
            # 启动动画
            self.animation_group.start()
            
            self.current_mode = self.CHAT_MODE
            
            # CHAT模式下设置背景圆角为21px
            self.bg_frame.setStyleSheet("background-color: #F7F7F7; border-radius: 21px;")
            
            # 发出状态变化信号
            self.mode_changed.emit(self.CHAT_MODE)
    
    def _after_collapse_animation(self):
        """从chat模式到message模式动画完成后启动定时器"""
        # 隐藏CHAT模式特有元素
        if hasattr(self, 'header_frame'):
            self.header_frame.hide()
        if hasattr(self, 'header_divider'):
            self.header_divider.hide()
        
        # 隐藏CHAT模式头部元素
        if hasattr(self, 'chat_title_label'):
            self.chat_title_label.hide()
        if hasattr(self, 'chat_logo'):
            self.chat_logo.hide()
        if hasattr(self, 'chat_collapse_btn'):
            self.chat_collapse_btn.hide()
        if hasattr(self, 'chat_settings_btn'):
            self.chat_settings_btn.hide()
        
        # 隐藏chat模式的聊天区域
        if hasattr(self, 'chat_area'):
            self.chat_area.hide()
        
        # 隐藏底部容器和消息栏
        self.bottom_container.hide()
        self.message_bar.hide()
        
        # 隐藏水平控制面板，显示垂直控制面板
        self.control_panel.hide()
        self.vertical_control_panel.show()
        
        # 显示MESSAGE模式元素
        self.logo_container.show()
        
        # 调整logo尺寸为message模式下的128px
        self.setLogoSize(128)
        
        # 创建或显示message模式的聊天区域
        if not hasattr(self, 'message_chat_area'):
            print("创建message模式聊天区域")
            # 创建message模式专用的聊天区域
            self.message_chat_area = QScrollArea(self.main_frame)
            self.message_chat_area.setGeometry(170+40, 31+40, 427, 105)  # 调整高度为105px
            self.message_chat_area.setStyleSheet("""
                background-color: transparent;
                border: none;
            """)
            self.message_chat_area.setWidgetResizable(True)
            self.message_chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.message_chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # 设置滚动条样式
            self.message_chat_area.verticalScrollBar().setStyleSheet("""
                QScrollBar:vertical {
                    background-color: #FFFFFF;
                    width: 8px;
                    margin: 0px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background-color: rgba(92, 118, 161, 180);
                    min-height: 30px;
                    border-radius: 4px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: rgba(71, 97, 139, 220);
                }
                QScrollBar::handle:vertical:pressed {
                    background-color: rgba(45, 72, 114, 250);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                    background: transparent;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: #FFFFFF;
                }
            """)
            
            # 创建聊天内容容器
            self.message_chat_container = QWidget()
            self.message_chat_container.setStyleSheet("""
                background-color: transparent;
                padding: 5px;
            """)
            
            # 设置聊天容器的布局
            self.message_chat_layout = QVBoxLayout(self.message_chat_container)
            self.message_chat_layout.setContentsMargins(15, 15, 15, 15)  # 四周都增加15px内边距
            self.message_chat_layout.setSpacing(10)
            self.message_chat_layout.setAlignment(Qt.AlignLeft)  # 更改为左对齐
            
            # 添加弹性空间，使最新消息始终在底部显示
            self.message_chat_layout.addStretch(1)
            
            # 将容器设置为滚动区域的部件
            self.message_chat_area.setWidget(self.message_chat_container)
            
            # 添加简化版的消息
            self.addSimplifiedMessage()
        else:
            # 如果message聊天区域已存在，调整位置并刷新消息
            print("刷新MESSAGE模式消息")
            self.message_chat_area.setGeometry(170+40, 31+40, 427, 105)  # 调整高度为105px
            
            # 清除现有消息
            if hasattr(self, 'message_chat_layout') and self.message_chat_layout:
                while self.message_chat_layout.count() > 1:  # 保留最后一个stretch
                    item = self.message_chat_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            
            # 重新添加简化消息
            self.addSimplifiedMessage()
        
        # 显示message模式的聊天区域
        self.message_chat_area.show()
        
        # 确保chat模式的元素隐藏
        if hasattr(self, 'chat_area'):
            self.chat_area.hide()
        if hasattr(self, 'header_frame'):
            self.header_frame.hide()
        if hasattr(self, 'header_divider'):
            self.header_divider.hide()
        self.message_bar.hide()
        
        # 为bg_frame重新应用阴影效果
        self.apply_shadow_to_bg_frame()
        
        # 启动10秒定时器，之后自动返回logo模式（从之前的3秒改为10秒）
        print("从chat模式切换到message模式后启动10秒计时器")
        self.timer.start(10000)
        
        # 启动进度圈倒计时
        self.progress_circle.start_countdown(10000)
    
    def _after_expand_animation(self):
        """从message模式到chat模式动画完成后的操作"""
        print("从message模式转换到chat模式完成")
        
        # 隐藏message模式的元素
        self.logo_container.hide()
        self.vertical_control_panel.hide()  # 隐藏垂直控制面板
        if hasattr(self, 'message_chat_area'):
            self.message_chat_area.hide()
        
        # 确保chat区域存在并设置正确
        if not hasattr(self, 'chat_area') or self.chat_area is None:
            print("创建chat模式聊天区域")
            self.setup_chat_area()
        else:
            # 设置chat区域位置和大小 - 确保与setup_chat_area方法中的尺寸一致
            self.chat_area.setGeometry(20, 83, 668, 585)  # 宽度668，高度564，在header下方
            # 确保消息已加载 - 不管是否有消息，都强制重新加载
            self.reloadMessages()
        
        # 确保删除旧的header_frame以重新创建
        if hasattr(self, 'header_frame') and self.header_frame is not None:
            # 如果不是我们创建的空占位符header_frame
            if self.header_frame.width() > 1:
                self.header_frame.deleteLater()
                self.header_frame = None
                print("删除旧的header_frame")
        
        # 显示聊天头部
        self.setupChatHeader()
        
        # 显示chat聊天区域
        self.chat_area.show()
        
        # 显示底部容器和消息输入栏
        self.bottom_container.show()
        self.message_bar.show()
        
        # 确保CHAT模式下背景圆角为21px
        self.bg_frame.setStyleSheet("background-color: #F7F7F7; border-radius: 21px;")
        
        # 为bg_frame重新应用阴影效果
        self.apply_shadow_to_bg_frame()
        
        print("完成chat模式UI设置")
        
        # 停止定时器，防止进入logo模式
        self.timer.stop()
    
    def setup_chat_area(self):
        """初始化chat模式的聊天区域"""
        # 创建chat模式专用的聊天区域
        self.chat_area = QScrollArea(self.bg_frame)
        # 调整位置和大小以匹配设计稿
        self.chat_area.setGeometry(20, 83, 668, 585)  # 根据设计稿调整位置和大小
        self.chat_area.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 21px;
            border: none;
        """)
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 设置滚动条样式
        self.chat_area.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                background-color: #FFFFFF;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(92, 118, 161, 180);
                min-height: 40px;
                border-radius: 5px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(71, 97, 139, 220);
            }
            QScrollBar::handle:vertical:pressed {
                background-color: rgba(45, 72, 114, 250);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
        # 创建聊天内容容器
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("""
            background-color: transparent;
            padding: 0px;
            border: none;
        """)
        
        # 设置聊天容器的布局
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)  # 根据设计稿调整内边距
        self.chat_layout.setSpacing(16)  # 根据设计稿调整消息间距
        self.chat_layout.setAlignment(Qt.AlignTop)  # 仅垂直从顶部开始，不设置水平对齐
        
        # 添加弹性空间，使最新消息始终在底部显示
        self.chat_layout.addStretch(1)
        
        # 将容器设置为滚动区域的部件
        self.chat_area.setWidget(self.chat_container)
        
        # 加载消息
        self.loadMessages()
    
    def addSimplifiedMessage(self):
        """为message模式添加简化的消息 - 只有文本，没有头像和气泡"""
        # 隐藏滚动条
        if hasattr(self, 'message_chat_area'):
            self.message_chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.message_chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 清除当前所有消息
        if hasattr(self, 'message_chat_layout'):
            while self.message_chat_layout.count() > 1:  # 保留最后一个stretch
                item = self.message_chat_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
        # 只显示第一条消息
        if len(self.messages) > 0 and hasattr(self, 'message_chat_container'):
            first_message = self.messages[0]
            
            # 获取消息内容并限制为前两行
            content = first_message["content"][:]
            lines = content.split('\n')
            if len(lines) > 2:
                # 只保留前两行，加上省略号
                content = '\n'.join(lines[:2]) + '...'
            
            # 创建纯文本标签，不使用气泡框架
            content_label = QLabel(self.message_chat_container)
            content_label.setText(content)
            # 设置自动换行但添加额外的最小宽度策略
            content_label.setWordWrap(True)
            content_label.setMinimumWidth(400)  # 强制标签至少需要这么宽才会换行
            content_label.setTextFormat(Qt.RichText)  # 强制使用富文本格式
            content_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)  # 允许选择和点击链接
            content_label.setStyleSheet("""
                color: #343434;
                font-family: 'PingFang SC';
                font-size: 27px;
                font-weight: 700;
                line-height: 48px;  /* 增加行高，使文本更加舒适 */
                letter-spacing: 0px;  /* 设置固定字间距 */
                background-color: transparent;
                padding: 0px;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            """)
            
            # 设置最大宽度并添加大小策略
            content_label.setMaximumWidth(400)
            content_label.setMaximumHeight(76)
            content_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
            
            # 将消息直接添加到布局中，左对齐
            self.message_chat_layout.insertWidget(self.message_chat_layout.count()-1, content_label, 0, Qt.AlignLeft)
    
    def setupChatHeader(self):
        """设置聊天模式的头部"""
        print("设置聊天模式头部")
        # 创建头部框架
        if not hasattr(self, 'header_frame') or self.header_frame is None:
            print("创建新的header_frame")
            
            # 获取脚本目录路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 添加Freeyou标题 - 由于移除了logo，标题位置调整
            self.chat_title_label = QLabel(self.bg_frame)
            self.chat_title_label.setGeometry(42-10, 7, 132+25, 69)  # 调整位置更靠左
            self.chat_title_label.setText("Freeyou")
            # 设置Pacifico字体
            try:
                from PyQt5.QtGui import QFont
                import sys
                # 获取主程序中加载的字体族名
                if 'loaded_families_pacifico' in globals() and loaded_families_pacifico:
                    self.chat_title_label.setFont(QFont(loaded_families_pacifico[0], 36))
                    font_family = loaded_families_pacifico[0]
                else:
                    self.chat_title_label.setFont(QFont("Pacifico", 36))
                    font_family = "Pacifico"
            except Exception as e:
                print("设置Pacifico字体失败：", e)
                font_family = "Pacifico"
            self.chat_title_label.setStyleSheet(f"""
                color: #274881;
                font-family: '{font_family}';
                font-size: 36px;
                font-weight: normal;
                line-height: normal;
                letter-spacing: 0.15em;
                background-color: transparent;
            """)
            
            # 移除logo相关代码，根据最新设计稿不再显示左上角logo
            
            # 关闭按钮 - 放在最右侧
            self.chat_close_btn = QPushButton(self.bg_frame)
            self.chat_close_btn.setGeometry(650, 19+5, 42, 42)  # 在折叠按钮右侧
            self.chat_close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF4D4F;
                    border: none;
                    border-radius: 21px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FF7875;
                }
            """)
            self.chat_close_btn.setText("X")
            self.chat_close_btn.clicked.connect(self.closeApplication)
            
            # 右侧控制按钮 - 直接放置在bg_frame上，不使用容器面板
            # 折叠按钮
            self.chat_collapse_btn = QPushButton(self.bg_frame)
            self.chat_collapse_btn.setGeometry(590, 19+5, 42, 42)  # 调整位置移到关闭按钮左侧
            self.chat_collapse_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background-color: rgba(39, 72, 129, 0.1);
                    border-radius: 12px;
                }
            """)

            collapse_path = os.path.join(script_dir, 'assets', 'front', 'collapse-diagonal-2-line.png')
            collapse_pixmap = QPixmap(collapse_path)
            collapse_icon = QIcon(collapse_pixmap)
            self.chat_collapse_btn.setIcon(collapse_icon)
            # 应用缩放因子
            icon_size = int(32 * self.icon_scale_factor)
            self.chat_collapse_btn.setIconSize(QSize(icon_size, icon_size))  # 使用缩放因子
            self.chat_collapse_btn.clicked.connect(self.toggleExpandCollapse)
            
            # 设置按钮
            self.chat_settings_btn = QPushButton(self.bg_frame)
            self.chat_settings_btn.setGeometry(530, 19+5, 42, 42)  # 调整位置，移到折叠按钮左侧
            self.chat_settings_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background-color: rgba(39, 72, 129, 0.1);
                    border-radius: 12px;
                }
            """)

            settings_path = os.path.join(script_dir, 'assets', 'front', 'settings-line.png')
            settings_pixmap = QPixmap(settings_path)
            settings_icon = QIcon(settings_pixmap)
            self.chat_settings_btn.setIcon(settings_icon)
            # 应用缩放因子
            settings_width = int(32 * self.icon_scale_factor)
            settings_height = int(36 * self.icon_scale_factor)
            self.chat_settings_btn.setIconSize(QSize(settings_width, settings_height))  # 使用缩放因子
            
            # 创建一个空的header_frame作为占位符，这样其他代码仍然可以引用它
            self.header_frame = QFrame(self.bg_frame)
            self.header_frame.setGeometry(0, 0, 1, 1)
            self.header_frame.setStyleSheet("background-color: transparent;")
            
            print("头部创建成功")
        
        # 显示头部
        self.chat_title_label.show()
        # 不再显示logo
        if hasattr(self, 'chat_logo'):
            self.chat_logo.hide()
        self.chat_close_btn.show()  # 显示关闭按钮
        self.chat_collapse_btn.show()
        self.chat_settings_btn.show()
        
        # 隐藏原来的控制面板和按钮
        self.control_panel.hide()
        
        print("显示header完成")
    
    def reloadMessages(self):
        """重新加载消息"""
        # 清除当前所有消息
        while self.chat_layout.count() > 1:  # 保留最后一个stretch
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 确保与setup_chat_area中保持一致的样式
        self.chat_container.setStyleSheet("""
            background-color: transparent;
            padding: 0px;
            border: none;
        """)
        
        # 保持与初始化时相同的内边距和间距
        self.chat_layout.setContentsMargins(20, 20, 20, 20)  # 根据设计稿调整内边距
        self.chat_layout.setSpacing(16)  # 根据设计稿调整消息间距
        
        # 重新加载所有消息
        for message in self.messages:
            self.addMessageBubble(message["sender"], message["content"])
            
        # 滚动到底部
        QTimer.singleShot(50, self.scrollToBottom)
    
    def enterLogoMode(self):
        # 进入logo模式
        if self.current_mode == self.MESSAGE_MODE:
            self.timer.stop()  # 停止定时器
            self.progress_circle.stop_countdown()  # 停止进度圈倒计时
            
            # 保存原始窗口位置
            self.original_window_pos = self.pos()
            
            # 先隐藏元素，然后再执行动画
            if hasattr(self, 'message_chat_area'):
                self.message_chat_area.hide()
            self.control_panel.hide()
            
            # 隐藏CHAT模式头部元素（即使在MESSAGE模式也要确保隐藏）
            if hasattr(self, 'chat_title_label'):
                self.chat_title_label.hide()
            if hasattr(self, 'chat_logo'):
                self.chat_logo.hide()
            if hasattr(self, 'chat_collapse_btn'):
                self.chat_collapse_btn.hide()
            if hasattr(self, 'chat_settings_btn'):
                self.chat_settings_btn.hide()
            
            # 创建不透明度效果 - 只应用于背景层
            self.opacity_effect = QGraphicsOpacityEffect(self.bg_frame)
            self.opacity_effect.setOpacity(1.0)  # 初始不透明
            self.bg_frame.setGraphicsEffect(self.opacity_effect)
            
            # 创建动画组
            self.logo_animation_group = QParallelAnimationGroup(self)
            
            # 窗口大小动画
            logo_size = 128  # 使用主logo大小，不是CHAT模式logo
            padding_size = 40*2  # 40px padding on each side
            target_size = QSize(self.logo_fixed_position.x() + logo_size + padding_size, 
                                self.logo_fixed_position.y() + logo_size + padding_size)
            
            self.window_resize = QPropertyAnimation(self, b"size")
            self.window_resize.setDuration(self.animation_duration)
            self.window_resize.setStartValue(self.size())
            self.window_resize.setEndValue(target_size)
            self.window_resize.setEasingCurve(QEasingCurve.OutQuint)
            
            # padding框架动画
            self.padding_anim = QPropertyAnimation(self.padding_frame, b"geometry")
            self.padding_anim.setDuration(self.animation_duration)
            self.padding_anim.setStartValue(self.padding_frame.geometry())
            self.padding_anim.setEndValue(QRect(0, 0, target_size.width(), target_size.height()))
            self.padding_anim.setEasingCurve(QEasingCurve.OutQuint)
            
            # 主框架动画
            main_frame_target_size = QSize(target_size.width() , target_size.height() )
            self.frame_anim = QPropertyAnimation(self.main_frame, b"geometry")
            self.frame_anim.setDuration(self.animation_duration)
            self.frame_anim.setStartValue(self.main_frame.geometry())
            self.frame_anim.setEndValue(QRect(0, 0, main_frame_target_size.width(), main_frame_target_size.height()))
            self.frame_anim.setEasingCurve(QEasingCurve.OutQuint)
            
            # 背景框架动画
            self.bg_frame_anim = QPropertyAnimation(self.bg_frame, b"geometry")
            self.bg_frame_anim.setDuration(self.animation_duration)
            self.bg_frame_anim.setStartValue(self.bg_frame.geometry())
            self.bg_frame_anim.setEndValue(QRect(40, 40, main_frame_target_size.width() - 80, main_frame_target_size.height() - 80))
            self.bg_frame_anim.setEasingCurve(QEasingCurve.OutQuint)
            
            # 背景透明度动画
            self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.opacity_anim.setDuration(self.animation_duration)
            self.opacity_anim.setStartValue(1.0)  # 完全不透明
            self.opacity_anim.setEndValue(0.0)    # 完全透明
            self.opacity_anim.setEasingCurve(QEasingCurve.OutQuint)
            
            # 添加动画到组
            self.logo_animation_group.addAnimation(self.window_resize)
            self.logo_animation_group.addAnimation(self.padding_anim)
            self.logo_animation_group.addAnimation(self.frame_anim)
            self.logo_animation_group.addAnimation(self.bg_frame_anim)
            self.logo_animation_group.addAnimation(self.opacity_anim)
            
            # 启动动画
            self.logo_animation_group.start()
            
            # 设置当前模式
            self.current_mode = self.LOGO_MODE
            
            # 发出状态变化信号
            self.mode_changed.emit(self.LOGO_MODE)
    
    def exitLogoMode(self):
        # 退出logo模式，回到message模式
        # 创建不透明度效果 - 只应用于背景层
        self.opacity_effect = QGraphicsOpacityEffect(self.bg_frame)
        self.opacity_effect.setOpacity(0.0)  # 初始透明
        self.bg_frame.setGraphicsEffect(self.opacity_effect)
        
        # 确保CHAT模式头部元素隐藏
        if hasattr(self, 'chat_title_label'):
            self.chat_title_label.hide()
        if hasattr(self, 'chat_logo'):
            self.chat_logo.hide()
        if hasattr(self, 'chat_collapse_btn'):
            self.chat_collapse_btn.hide()
        if hasattr(self, 'chat_settings_btn'):
            self.chat_settings_btn.hide()
        
        # 创建动画组
        self.exit_logo_animation = QParallelAnimationGroup(self)
        
        # 窗口大小动画
        self.window_resize = QPropertyAnimation(self, b"size")
        self.window_resize.setDuration(self.animation_duration)
        self.window_resize.setStartValue(self.size())
        self.window_resize.setEndValue(QSize(708+80, 171+80))  # 708+20, 171+20 向外扩展10px
        self.window_resize.setEasingCurve(QEasingCurve.OutQuint)
        
        # padding框架动画
        self.padding_anim = QPropertyAnimation(self.padding_frame, b"geometry")
        self.padding_anim.setDuration(self.animation_duration)
        self.padding_anim.setStartValue(self.padding_frame.geometry())
        self.padding_anim.setEndValue(QRect(0, 0, 708+80, 171+80))
        self.padding_anim.setEasingCurve(QEasingCurve.OutQuint)
        
        # 主框架动画
        self.frame_anim = QPropertyAnimation(self.main_frame, b"geometry")
        self.frame_anim.setDuration(self.animation_duration)
        self.frame_anim.setStartValue(self.main_frame.geometry())
        self.frame_anim.setEndValue(QRect(0, 0, 708+80, 171+80))
        self.frame_anim.setEasingCurve(QEasingCurve.OutQuint)
        
        # 背景框架动画
        self.bg_frame_anim = QPropertyAnimation(self.bg_frame, b"geometry")
        self.bg_frame_anim.setDuration(self.animation_duration)
        self.bg_frame_anim.setStartValue(self.bg_frame.geometry())
        self.bg_frame_anim.setEndValue(QRect(40, 40, 708, 171))
        self.bg_frame_anim.setEasingCurve(QEasingCurve.OutQuint)
        
        # 背景透明度动画
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(self.animation_duration)
        self.opacity_anim.setStartValue(0.0)  # 完全透明
        self.opacity_anim.setEndValue(1.0)    # 完全不透明
        self.opacity_anim.setEasingCurve(QEasingCurve.OutQuint)
        
        # 添加动画到组
        self.exit_logo_animation.addAnimation(self.window_resize)
        self.exit_logo_animation.addAnimation(self.padding_anim)
        self.exit_logo_animation.addAnimation(self.frame_anim)
        self.exit_logo_animation.addAnimation(self.bg_frame_anim)
        self.exit_logo_animation.addAnimation(self.opacity_anim)
        
        # 设置动画完成后的操作 - 添加启动定时器的回调
        self.exit_logo_animation.finished.connect(lambda: self._after_exit_logo_animation())
        
        # 启动动画
        self.exit_logo_animation.start()
        
        # 设置当前模式
        self.current_mode = self.MESSAGE_MODE
        
        # MESSAGE模式下设置背景圆角为38px
        self.bg_frame.setStyleSheet("background-color: #F7F7F7; border-radius: 38px;")
        
        # 发出状态变化信号
        self.mode_changed.emit(self.MESSAGE_MODE)
    
    def _after_exit_logo_animation(self):
        """从logo模式到message模式动画完成后的操作"""
        # 显示message模式的必要元素
        self.logo_container.show()
        
        # 调整logo尺寸为message模式下的128px
        self.setLogoSize(128)
        
        self.vertical_control_panel.show()  # 显示垂直控制面板而不是水平的
        
        # 确保CHAT模式头部元素隐藏
        if hasattr(self, 'chat_title_label'):
            self.chat_title_label.hide()
        if hasattr(self, 'chat_logo'):
            self.chat_logo.hide()
        if hasattr(self, 'chat_collapse_btn'):
            self.chat_collapse_btn.hide()
        if hasattr(self, 'chat_settings_btn'):
            self.chat_settings_btn.hide()
        
        # 确保message聊天区域调整到正确的大小和位置
        if not hasattr(self, 'message_chat_area'):
            # 如果message模式的聊天区域不存在，创建它
            print("创建message模式聊天区域")
            # 创建message模式专用的聊天区域
            self.message_chat_area = QScrollArea(self.main_frame)
            self.message_chat_area.setGeometry(170+40, 31+40, 427, 105)  # 调整高度为105px
            self.message_chat_area.setStyleSheet("""
                background-color: transparent;
                border: none;
            """)
            self.message_chat_area.setWidgetResizable(True)
            self.message_chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.message_chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # 设置滚动条样式
            self.message_chat_area.verticalScrollBar().setStyleSheet("""
                QScrollBar:vertical {
                    background-color: #FFFFFF;
                    width: 8px;
                    margin: 0px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background-color: rgba(92, 118, 161, 180);
                    min-height: 30px;
                    border-radius: 4px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: rgba(71, 97, 139, 220);
                }
                QScrollBar::handle:vertical:pressed {
                    background-color: rgba(45, 72, 114, 250);
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                    background: transparent;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: #FFFFFF;
                }
            """)
            
            # 创建聊天内容容器
            self.message_chat_container = QWidget()
            self.message_chat_container.setStyleSheet("""
                background-color: transparent;
                padding: 5px;
            """)
            
            # 设置聊天容器的布局
            self.message_chat_layout = QVBoxLayout(self.message_chat_container)
            self.message_chat_layout.setContentsMargins(15, 15, 15, 15)  # 四周都增加15px内边距
            self.message_chat_layout.setSpacing(10)
            self.message_chat_layout.setAlignment(Qt.AlignLeft)  # 更改为左对齐
            
            # 添加弹性空间，使最新消息始终在底部显示
            self.message_chat_layout.addStretch(1)
            
            # 将容器设置为滚动区域的部件
            self.message_chat_area.setWidget(self.message_chat_container)
            
            # 添加简化版的消息
            self.addSimplifiedMessage()
        else:
            # 如果message聊天区域已存在，调整位置并刷新消息
            print("刷新MESSAGE模式消息")
            self.message_chat_area.setGeometry(170+40, 31+40, 427, 105)  # 调整高度为105px
            
            # 清除现有消息
            if hasattr(self, 'message_chat_layout') and self.message_chat_layout:
                while self.message_chat_layout.count() > 1:  # 保留最后一个stretch
                    item = self.message_chat_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            
            # 重新添加简化消息
            self.addSimplifiedMessage()
        
        # 显示message模式的聊天区域
        self.message_chat_area.show()
        
        # 将滚动条拉到顶部
        if hasattr(self, 'message_chat_area') and self.message_chat_area is not None:
            self.message_chat_area.verticalScrollBar().setValue(0)
            print("将消息滚动条设置到顶部")
        
        # 确保chat模式的元素隐藏
        if hasattr(self, 'chat_area'):
            self.chat_area.hide()
        if hasattr(self, 'header_frame'):
            self.header_frame.hide()
        if hasattr(self, 'header_divider'):
            self.header_divider.hide()
        self.message_bar.hide()
        
        # 确保MESSAGE模式下背景圆角为38px
        self.bg_frame.setStyleSheet("background-color: #F7F7F7; border-radius: 38px;")
        
        # 为bg_frame重新应用阴影效果
        self.apply_shadow_to_bg_frame()
        
        # 启动10秒定时器，之后自动返回logo模式
        print("从logo模式切换到message模式后启动10秒计时器")
        self.timer.start(10000)
        
        # 启动进度圈倒计时
        self.progress_circle.start_countdown(10000)
    
    def apply_shadow_to_bg_frame(self):
        """为背景框架应用阴影效果"""
        # 定义阴影参数 - 匹配设计稿
        shadow_color = QColor(39, 72, 129, 135)  # rgba(0, 0, 0, 0.3)
        shadow_offset_y = 0
        shadow_blur_radius = 40
        
        # 创建阴影效果
        bg_shadow = QGraphicsDropShadowEffect()
        bg_shadow.setBlurRadius(shadow_blur_radius)
        bg_shadow.setColor(shadow_color)
        bg_shadow.setOffset(0, shadow_offset_y)
        
        # 移除之前的效果（如果有）
        old_effect = self.bg_frame.graphicsEffect()
        if old_effect is not None:
            old_effect.setEnabled(False)
        
        # 应用新的阴影效果
        self.bg_frame.setGraphicsEffect(bg_shadow)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            
            # 点击时如果在logo模式，退出logo模式
            if self.current_mode == self.LOGO_MODE:
                self.exitLogoMode()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def sendMessage(self):
        """发送用户消息并添加到聊天区域"""
        message_text = self.input_field.text().strip()
        if message_text:
            # 添加用户消息到列表
            self.messages.append({"sender": "user", "content": message_text})
            
            # 清空输入框
            self.input_field.clear()
            
            # 添加消息气泡到聊天区域
            self.addMessageBubble("user", message_text)
            
            # 模拟AI响应
            QTimer.singleShot(1000, self.simulateResponse)
            
            # 滚动到底部
            self.scrollToBottom()
    
    def simulateResponse(self):
        """向后端发送请求，获取AI响应"""
        # 获取最新的用户消息
        if len(self.messages) > 0 and self.messages[-1]["sender"] == "user":
            user_message = self.messages[-1]["content"]
            
            # 创建并启动请求线程
            self.chat_request_thread = ChatRequestThread(user_message)
            self.chat_request_thread.response_received.connect(self.handleChatResponse)
            self.chat_request_thread.error_occurred.connect(self.handleChatError)
            self.chat_request_thread.start()
            
            # 添加一个临时"正在输入"消息
            self.addMessageBubble("agent", "正在思考...")
            # 保存临时消息的引用，以便稍后替换
            self.typing_bubble = self.chat_layout.itemAt(self.chat_layout.count() - 2).widget()
        else:
            # 如果没有用户消息，添加一个默认响应
            self.addMessageBubble("agent", "我没有收到您的消息，请重新输入。")
    
    def handleChatResponse(self, response_text):
        """处理从后端接收的响应"""
        # 移除"正在输入"消息
        if hasattr(self, 'typing_bubble') and self.typing_bubble:
            index = self.chat_layout.indexOf(self.typing_bubble)
            if index >= 0:
                self.chat_layout.takeAt(index)
                self.typing_bubble.deleteLater()
                self.typing_bubble = None
        
        # 添加AI响应到消息列表
        self.messages.append({"sender": "agent", "content": response_text})
        
        # 添加消息气泡到聊天区域
        self.addMessageBubble("agent", response_text)
        
        # 确保滚动到底部
        self.scrollToBottom()
    
    def handleChatError(self, error_message):
        """处理聊天请求错误"""
        # 移除"正在输入"消息
        if hasattr(self, 'typing_bubble') and self.typing_bubble:
            index = self.chat_layout.indexOf(self.typing_bubble)
            if index >= 0:
                self.chat_layout.takeAt(index)
                self.typing_bubble.deleteLater()
                self.typing_bubble = None
        
        # 添加错误消息到消息列表
        self.messages.append({"sender": "agent", "content": error_message})
        
        # 添加错误消息气泡到聊天区域
        self.addMessageBubble("agent", error_message)
        
        # 确保滚动到底部
        self.scrollToBottom()
    
    def addMessageBubble(self, sender, content):
        """添加消息气泡到当前活跃的聊天区域"""
        # 根据当前模式创建消息气泡
        is_chat_mode = (self.current_mode == self.CHAT_MODE)
        bubble = MessageBubble(sender, content, is_chat_mode=is_chat_mode)
        
        # 确定当前活跃的聊天区域
        if self.current_mode == self.CHAT_MODE and hasattr(self, 'chat_layout'):
            # 在Chat模式下
            if sender == "user":
                # 用户消息左对齐，增加最大宽度
                bubble.setMaximumWidth(600)  # 从550增加到600
                # 在stretch前插入消息，确保在底部显示
                self.chat_layout.insertWidget(self.chat_layout.count()-1, bubble, 0, Qt.AlignLeft)
            else:
                # AI消息左对齐，增加最大宽度
                bubble.setMaximumWidth(600)  # 从550增加到600
                # 在stretch前插入消息，确保在底部显示
                self.chat_layout.insertWidget(self.chat_layout.count()-1, bubble, 0, Qt.AlignLeft)
            
            # 确保滚动条可见并滚动到底部
            if hasattr(self, 'chat_area'):
                self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                QTimer.singleShot(50, self.scrollToBottom)
        elif self.current_mode == self.MESSAGE_MODE and hasattr(self, 'message_chat_layout'):
            # 在Message模式下，保持原有宽度
            bubble.setMaximumWidth(400)
            
            if sender == "user":
                self.message_chat_layout.insertWidget(self.message_chat_layout.count()-1, bubble, 0, Qt.AlignLeft)
            else:
                self.message_chat_layout.insertWidget(self.message_chat_layout.count()-1, bubble, 0, Qt.AlignLeft)
            
            # 确保滚动条可见并滚动到底部
            if hasattr(self, 'message_chat_area'):
                self.message_chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                QTimer.singleShot(50, self.message_scrollToBottom)
                
    def scrollToBottom(self):
        """滚动聊天区域到底部，确保显示最新消息"""
        if hasattr(self, 'chat_area') and self.chat_area is not None:
            self.chat_area.verticalScrollBar().setValue(
                self.chat_area.verticalScrollBar().maximum()
            )
            
    def message_scrollToBottom(self):
        """滚动message模式的聊天区域到底部"""
        if hasattr(self, 'message_chat_area') and self.message_chat_area is not None:
            self.message_chat_area.verticalScrollBar().setValue(
                self.message_chat_area.verticalScrollBar().maximum()
            )
    
    def enterEvent(self, event):
        """鼠标进入窗口事件"""
        super().enterEvent(event)
        # 显示滚动条
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def leaveEvent(self, event):
        """鼠标离开窗口事件"""
        super().leaveEvent(event)

    def loadMessages(self):
        """加载初始消息到chat区域"""
        if hasattr(self, 'chat_layout'):
            for message in self.messages:
                bubble = MessageBubble(message["sender"], message["content"], is_chat_mode=True)
                bubble.setMaximumWidth(600)  # 与addMessageBubble方法一致
                
                if message["sender"] == "user":
                    self.chat_layout.insertWidget(self.chat_layout.count()-1, bubble, 0, Qt.AlignLeft)
                else:
                    self.chat_layout.insertWidget(self.chat_layout.count()-1, bubble, 0, Qt.AlignLeft)
            
            # 滚动到底部
            if hasattr(self, 'chat_area'):
                QTimer.singleShot(50, self.scrollToBottom)
    
    def setLogoSize(self, size):
        """设置logo的尺寸
        
        Args:
            size (int): logo的尺寸大小，单位为像素
        """
        self.logo_container.setGeometry(20+40, 20+40, size, size)
        self.logo_label.setGeometry(0, 0, size, size)
        
        # 根据尺寸调整圆角半径
        radius = size // 2
        self.logo_container.radius = radius
        self.logo_label.setStyleSheet(f"border-radius: {radius}px; border: none; background-color: transparent;")
        self.logo_label.show()
        # 设置阴影效果 - 根据模式不同设置
        if size == 128:  # MESSAGE模式
            # 为MESSAGE模式设置阴影效果 - 蓝色阴影
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)  # 10px模糊
            shadow.setColor(QColor(45, 123, 186, 76))  # rgba(45, 123, 186, 0.3) - 蓝色阴影
            shadow.setOffset(0, 4)  # 垂直偏移4px
            self.logo_container.setGraphicsEffect(shadow)
        else:  # CHAT模式
            # 移除阴影效果
            self.logo_container.setGraphicsEffect(None)

    def createDefaultLogo(self):
        """创建一个默认的Logo图像"""
        pixmap = QPixmap(60, 60)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 画圆形蓝色背景
        painter.setBrush(QBrush(QColor("#2D7BBA")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 60, 60)
        
        # 添加文字标识
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 30, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "F")
        
        painter.end()
        
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setScaledContents(True)
    
    def createDefaultCollapseButton(self):
        """创建一个默认的折叠按钮图标"""
        pixmap = QPixmap(26, 26)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置画笔
        painter.setPen(QPen(QColor("#333333"), 2))
        
        # 画一个简化的折叠图标 (菱形)
        painter.drawLine(13, 5, 22, 13)  # 右上斜线
        painter.drawLine(22, 13, 13, 22)  # 右下斜线
        painter.drawLine(13, 22, 5, 13)   # 左下斜线
        painter.drawLine(5, 13, 13, 5)    # 左上斜线
        
        # 画一个中心点
        painter.setBrush(QBrush(QColor("#333333")))
        painter.drawEllipse(11, 11, 4, 4)
        
        painter.end()
        
        self.collapse_btn.setIcon(QIcon(pixmap))
        # 应用图标缩放因子
        collapse_size = int(26 * self.icon_scale_factor)
        self.collapse_btn.setIconSize(QSize(collapse_size, collapse_size))
    
    def createDefaultSettingsButton(self):
        """创建一个默认的设置按钮图标"""
        pixmap = QPixmap(26, 26)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置画笔
        painter.setPen(QPen(QColor("#333333"), 2))
        
        # 画一个简化的设置图标 (齿轮)
        painter.drawEllipse(8, 8, 10, 10)  # 中心圆
        
        # 画八个小齿轮
        for i in range(8):
            angle = i * 45
            rad_angle = angle * 3.14159 / 180
            x1 = 13 + 5 * math.cos(rad_angle)
            y1 = 13 + 5 * math.sin(rad_angle)
            x2 = 13 + 10 * math.cos(rad_angle)
            y2 = 13 + 10 * math.sin(rad_angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        painter.end()
        
        self.settings_btn.setIcon(QIcon(pixmap))
        # 应用图标缩放因子
        settings_size = int(26 * self.icon_scale_factor)
        self.settings_btn.setIconSize(QSize(settings_size, settings_size))

    def createDefaultCollapseIcon(self, button):
        """为任何按钮创建一个默认的折叠图标"""
        pixmap = QPixmap(26, 26)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置画笔
        painter.setPen(QPen(QColor("#333333"), 2))
        
        # 画一个简化的折叠图标 (菱形)
        painter.drawLine(13, 5, 22, 13)  # 右上斜线
        painter.drawLine(22, 13, 13, 22)  # 右下斜线
        painter.drawLine(13, 22, 5, 13)   # 左下斜线
        painter.drawLine(5, 13, 13, 5)    # 左上斜线
        
        # 画一个中心点
        painter.setBrush(QBrush(QColor("#333333")))
        painter.drawEllipse(11, 11, 4, 4)
        
        painter.end()
        
        button.setIcon(QIcon(pixmap))
    
    def createDefaultCollapseButton(self):
        """创建一个默认的折叠按钮图标"""
        self.createDefaultCollapseIcon(self.collapse_btn)

class FocusShadowLineEdit(QLineEdit):
    def __init__(self, parent=None, message_bar=None):
        super().__init__(parent)
        self.message_bar = message_bar

    def focusInEvent(self, event):
        if self.message_bar:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(30)
            shadow.setColor(QColor(39, 72, 129, 45))
            shadow.setOffset(0, 0)
            self.message_bar.setGraphicsEffect(shadow)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        if self.message_bar:
            self.message_bar.setGraphicsEffect(None)
        super().focusOutEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 创建必要的目录结构
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for directory in ['assets/fonts/ttf', 'assets/front', 'assets/demo_pic', 'sense_env/pic', 'sense_env/ocr', 'sense_env/describe', 'sense_env/sense']:
        dir_path = os.path.join(script_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"创建目录: {dir_path}")

    # 加载并设置全局字体 
    font_found = False
    font_path_main = os.path.join(script_dir, 'assets', 'fonts', 'ttf', 'PingFangSC-Medium.ttf')
    
    # 如果字体文件不存在，使用系统默认字体
    if os.path.exists(font_path_main):
        font_id_main = QFontDatabase.addApplicationFont(font_path_main)
        if font_id_main != -1:
            loaded_families_main = QFontDatabase.applicationFontFamilies(font_id_main)
            print("已加载主字体：", loaded_families_main)
            if loaded_families_main:
                app.setFont(QFont(loaded_families_main[0]))
                font_found = True
        
    if not font_found:
        print("使用系统默认字体")
        default_font = QFont()
        default_font.setFamily("Arial")  # 使用通用字体
        default_font.setPointSize(12)
        app.setFont(default_font)

    # 加载 Pacifico-Regular.ttf 字体或使用默认替代
    pacifico_found = False
    font_path_pacifico = os.path.join(script_dir, 'assets', 'fonts', 'ttf', 'Pacifico-Regular.ttf')
    
    if os.path.exists(font_path_pacifico):
        font_id_pacifico = QFontDatabase.addApplicationFont(font_path_pacifico)
        if font_id_pacifico != -1:
            loaded_families_pacifico = QFontDatabase.applicationFontFamilies(font_id_pacifico)
            print("已加载Pacifico字体：", loaded_families_pacifico)
            pacifico_found = True
        else:
            loaded_families_pacifico = []
            print("Pacifico字体加载失败，使用替代字体")
    else:
        loaded_families_pacifico = []
        print("Pacifico字体文件不存在，使用替代字体")
    
    if not pacifico_found:
        # 设置替代字体
        if platform.system() == 'Darwin':  # macOS
            loaded_families_pacifico = ["Zapfino"]  # macOS上的艺术字体
        else:
            loaded_families_pacifico = ["Comic Sans MS"]  # Windows/Linux上的替代字体

    # 创建应用的视图部分
    view = FreeYouApp()
    
    # 创建截图服务
    screenshot_service = ScreenshotService()
    
    # 创建控制器 - 连接服务和视图
    controller = ScreenshotServiceController(screenshot_service, view)
    
    # 处理 Control+C 信号
    def signal_handler(sig, frame):
        print("收到 Control+C 信号，正在关闭程序...")
        QApplication.quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # 启用信号处理
    # 创建一个定时器以定期处理Python信号
    timer = QTimer()
    timer.start(500)  # 每500毫秒检查一次信号
    timer.timeout.connect(lambda: None)  # 空连接，但允许Python处理信号
    
    sys.exit(app.exec_()) 
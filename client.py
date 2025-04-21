# 机器人客户端示例代码
import cv2
import base64
import json
import websocket
import threading
import time
import numpy as np

# 配置项
SERVER_URL = "ws://172.20.39.181:1234/ws/robot/robot_123"
FRAME_RATE = 10  # 每秒10帧，可根据网络状况调整
FRAME_WIDTH = 640  # 视频帧宽度
FRAME_HEIGHT = 480  # 视频帧高度
JPEG_QUALITY = 70  # JPEG压缩质量(0-100)

# 全局变量
running = True
ws = None
robot_status = {
    "battery": 85,
    "position": {"x": 0, "y": 0},
    "harvested_count": 0
}

# 处理收到的控制命令
def handle_command(command_data):
    cmd = command_data.get("command")
    params = command_data.get("params", {})
    
    print(f"收到命令: {cmd}, 参数: {params}")
    
    # 根据不同命令执行不同操作
    if cmd == "forward":
        # 实现前进逻辑
        print("机器人前进")
    elif cmd == "backward":
        # 实现后退逻辑
        print("机器人后退")
    elif cmd == "left":
        # 实现左转逻辑
        print("机器人左转")
    elif cmd == "right":
        # 实现右转逻辑
        print("机器人右转")
    elif cmd == "stop":
        # 实现停止逻辑
        print("机器人停止")
    elif cmd == "start_harvest":
        # 开始采摘
        print("开始采摘")
    elif cmd == "pause_harvest":
        # 暂停采摘
        print("暂停采摘")
    elif cmd == "emergency_stop":
        # 紧急停止
        print("紧急停止所有操作")

# WebSocket接收消息处理
def on_message(ws, message):
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "command":
            handle_command(data)
        
    except Exception as e:
        print(f"处理消息错误: {e}")

def on_error(ws, error):
    print(f"WebSocket错误: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket连接关闭")
    # 可以添加重连逻辑

def on_open(ws):
    print("WebSocket连接已建立")
    
    # 发送初始状态
    ws.send(json.dumps({
        "type": "status_update",
        "data": robot_status
    }))

# 状态更新线程
def status_update_thread():
    while running:
        try:
            if ws and ws.sock and ws.sock.connected:
                # 更新机器人状态
                robot_status["battery"] -= 0.01  # 模拟电池消耗
                robot_status["harvested_count"] += 1  # 模拟采摘计数
                
                # 发送状态更新
                ws.send(json.dumps({
                    "type": "status_update",
                    "data": robot_status
                }))
        except Exception as e:
            print(f"状态更新错误: {e}")
        
        time.sleep(5)  # 每5秒更新一次状态

# 视频传输线程
def video_streaming_thread():
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    frame_interval = 1.0 / FRAME_RATE
    last_frame_time = time.time()
    
    while running and cap.isOpened():
        # 控制帧率
        current_time = time.time()
        if current_time - last_frame_time < frame_interval:
            time.sleep(0.001)  # 短暂休眠以减少CPU使用
            continue
            
        last_frame_time = current_time
        
        # 读取视频帧
        ret, frame = cap.read()
        if not ret:
            print("无法获取视频帧")
            break
            
        try:
            # 压缩帧为JPEG格式
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            # 转为Base64编码
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            
            # 检查WebSocket连接状态
            if ws and ws.sock and ws.sock.connected:
                # 发送视频帧
                ws.send(json.dumps({
                    "type": "video_frame",
                    "data": jpg_as_text
                }))
        except Exception as e:
            print(f"处理视频帧错误: {e}")
    
    # 释放摄像头
    cap.release()

# 主函数
def main():
    global ws, running
    
    # 创建WebSocket连接
    ws = websocket.WebSocketApp(SERVER_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    # 创建并启动状态更新线程
    status_thread = threading.Thread(target=status_update_thread)
    status_thread.daemon = True
    status_thread.start()
    
    # 创建并启动视频传输线程
    video_thread = threading.Thread(target=video_streaming_thread)
    video_thread.daemon = True
    video_thread.start()
    
    # 启动WebSocket连接（阻塞）
    ws.run_forever()
    
    # 当WebSocket连接关闭时，设置running为False以停止其他线程
    running = False
    
    # 等待其他线程结束
    status_thread.join()
    video_thread.join()

if __name__ == "__main__":
    try:
        main()
        a = 1
    except KeyboardInterrupt:
        print("程序被用户中断")
        running = False
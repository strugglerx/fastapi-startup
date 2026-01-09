#!/bin/bash

# 设置错误时退出
set -e

# 记录PID文件路径
PID_FILE="/tmp/uvicorn.pid"

# 优雅关闭函数
graceful_shutdown() {
    echo "正在优雅关闭服务..."
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "发送SIGTERM信号到进程 $PID"
            kill -TERM "$PID"
            # 等待进程退出
            for i in {1..30}; do
                if ! kill -0 "$PID" 2>/dev/null; then
                    echo "进程已优雅退出"
                    break
                fi
                sleep 1
            done
            # 如果仍未退出，强制杀死
            if kill -0 "$PID" 2>/dev/null; then
                echo "强制终止进程 $PID"
                kill -9 "$PID"
            fi
        fi
        rm -f "$PID_FILE"
    fi
}

# 设置信号处理
trap graceful_shutdown SIGTERM SIGINT

# 启动函数
start_server() {
    echo "启动uvicorn服务器..."
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --timeout-keep-alive 300 \
        --http h11 \
        --no-server-header \
        --access-log \
        --log-level info &
    
    # 记录PID
    echo $! > "$PID_FILE"
    echo "服务器启动，PID: $(cat $PID_FILE)"
    
    # 等待后台进程
    wait $!
}

# 主循环
while true; do
    start_server
    EXIT_CODE=$?
    
    echo "进程退出，退出码: $EXIT_CODE"
    
    # 清理PID文件
    rm -f "$PID_FILE"
    
    # 如果是正常退出或被信号终止，则不重启
    if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 130 ] || [ $EXIT_CODE -eq 143 ]; then
        echo "正常退出，不重启"
        break
    fi
    
    echo "10秒后重启..."
    sleep 10
done
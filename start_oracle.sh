#!/bin/bash

# OpenOracle 启动脚本
# 版本: 1.0.0
# 作者: OpenOracle Core Team

set -e  # 出错时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查环境
check_environment() {
    log_info "检查系统环境..."
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ $PYTHON_VERSION < 3.9 ]]; then
            log_error "需要Python 3.9或更高版本，当前版本: $PYTHON_VERSION"
            exit 1
        fi
        log_success "Python版本: $PYTHON_VERSION"
    else
        log_error "未找到Python3"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_warning "未找到虚拟环境，正在创建..."
        python3 -m venv venv
        log_success "虚拟环境创建成功"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    log_success "虚拟环境已激活"
    
    # 检查依赖
    if [ ! -f "requirements.txt" ]; then
        log_error "未找到requirements.txt文件"
        exit 1
    fi
}

# 安装依赖
install_dependencies() {
    log_info "安装依赖包..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if pip install -r requirements.txt; then
        log_success "依赖安装成功"
    else
        log_error "依赖安装失败"
        exit 1
    fi
}

# 运行健康检查
run_health_check() {
    log_info "运行系统健康检查..."
    
    if python src/core/health_check.py; then
        log_success "健康检查通过"
    else
        log_error "健康检查失败，请查看日志"
        exit 1
    fi
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    if python scripts/init_db.py; then
        log_success "数据库初始化成功"
    else
        log_error "数据库初始化失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_info "启动OpenOracle服务..."
    
    # 创建日志目录
    mkdir -p logs
    
    # 启动服务
    SERVICES=(
        "API服务:uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload"
        "任务队列:celery -A src.tasks worker --loglevel=info"
        "监控服务:python src/monitoring/monitor.py"
    )
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r service_name command <<< "$service"
        log_info "启动 $service_name..."
        
        # 在后台启动服务
        eval "$command >> logs/${service_name// /_}.log 2>&1 &"
        PID=$!
        echo $PID > "pids/${service_name// /_}.pid"
        
        # 等待服务启动
        sleep 2
        if ps -p $PID > /dev/null; then
            log_success "$service_name 启动成功 (PID: $PID)"
        else
            log_error "$service_name 启动失败"
        fi
    done
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    sleep 5  # 给服务启动时间
    
    # 检查API服务
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "API服务运行正常"
    else
        log_error "API服务无响应"
    fi
    
    # 检查数据库连接
    if python scripts/check_db.py; then
        log_success "数据库连接正常"
    else
        log_error "数据库连接失败"
    fi
    
    # 检查区块链连接
    if python scripts/check_blockchain.py; then
        log_success "区块链连接正常"
    else
        log_error "区块链连接失败"
    fi
}

# 显示系统信息
show_system_info() {
    log_info "系统信息:"
    echo "========================================"
    echo "OpenOracle 版本: 1.0.0"
    echo "启动时间: $(date)"
    echo "API地址: http://localhost:8000"
    echo "文档地址: http://localhost:8000/docs"
    echo "监控地址: http://localhost:8000/monitor"
    echo "日志目录: ./logs/"
    echo "PID文件: ./pids/"
    echo "========================================"
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    
    if [ -d "pids" ]; then
        for pidfile in pids/*.pid; do
            if [ -f "$pidfile" ]; then
                PID=$(cat "$pidfile")
                if kill -0 $PID 2>/dev/null; then
                    kill $PID
                    log_success "停止进程: $PID ($(basename "$pidfile" .pid))"
                fi
                rm "$pidfile"
            fi
        done
    fi
}

# 清理函数
cleanup() {
    log_info "执行清理..."
    stop_services
    log_success "清理完成"
}

# 设置信号处理
trap cleanup EXIT INT TERM

# 主函数
main() {
    echo -e "${GREEN}"
    echo "========================================"
    echo "      OpenOracle 系统启动程序"
    echo "========================================"
    echo -e "${NC}"
    
    # 创建必要目录
    mkdir -p logs pids data
    
    # 执行步骤
    check_environment
    install_dependencies
    run_health_check
    init_database
    start_services
    check_services
    show_system_info
    
    log_success "OpenOracle 系统启动完成！"
    
    # 保持脚本运行
    log_info "按 Ctrl+C 停止服务"
    while true; do
        sleep 1
    done
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
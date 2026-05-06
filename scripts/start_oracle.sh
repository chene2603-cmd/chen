#!/bin/bash
# OpenOracle 一键启动脚本

set -e

echo "╔══════════════════════════════════════════╗"
echo "║     OpenOracle 系统启动脚本              ║"
echo "╚══════════════════════════════════════════╝"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 未检测到 Docker，请先安装 Docker。"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    # 尝试 docker compose (新版本)
    if docker compose version &> /dev/null; then
        alias docker-compose="docker compose"
    else
        echo "❌ 未检测到 docker-compose。"
        exit 1
    fi
fi

# 创建必要目录
mkdir -p logs data config

# 解析参数
MODE=${1:-dev}  # 默认为开发模式

case $MODE in
    dev)
        echo "🚀 以开发模式启动..."
        # 仅启动核心服务 + 本地链 + IPFS
        docker-compose up -d oracle-api hardhat-node ipfs
        echo "✅ API 服务: http://localhost:8000"
        echo "✅ API 文档: http://localhost:8000/docs"
        echo "✅ 本地链:   http://localhost:8545"
        echo "✅ IPFS:     http://localhost:5001"
        ;;

    deploy)
        echo "📜 部署智能合约到本地链..."
        docker-compose --profile deploy up -d
        ;;

    prod)
        echo "🏭 以生产模式启动..."
        docker-compose --profile prod up -d
        echo "✅ 服务已启动（通过 Nginx 代理）"
        ;;

    monitoring)
        echo "📊 启动监控栈..."
        docker-compose --profile monitoring up -d prometheus grafana
        echo "✅ Prometheus: http://localhost:9090"
        echo "✅ Grafana:    http://localhost:3000 (admin/admin)"
        ;;

    stop)
        echo "🛑 停止所有服务..."
        docker-compose down
        ;;

    logs)
        echo "📋 显示日志..."
        docker-compose logs -f oracle-api
        ;;

    *)
        echo "用法: $0 {dev|deploy|prod|monitoring|stop|logs}"
        echo ""
        echo "  dev        - 开发模式（API + 本地链 + IPFS）"
        echo "  deploy     - 部署智能合约"
        echo "  prod       - 生产模式（含 Nginx）"
        echo "  monitoring - 启动监控栈"
        echo "  stop       - 停止所有服务"
        echo "  logs       - 查看 API 日志"
        exit 1
        ;;
esac
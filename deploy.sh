#!/bin/bash

# 刷题通部署脚本

echo "=== 刷题通部署 ==="

# 创建数据目录
mkdir -p ./data

# 构建并启动 Docker 容器
echo "正在构建 Docker 镜像..."
docker-compose build

echo "正在启动服务..."
docker-compose up -d

echo ""
echo "部署完成！"
echo "访问地址: http://你的服务器IP:4000"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
echo "数据备份："
echo "  备份 data 目录即可保存所有数据"

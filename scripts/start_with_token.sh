#!/bin/bash
if [ -z "$1" ]; then
    echo "请提供 Cloudflare Tunnel Token。"
    echo "用法: ./scripts/start_with_token.sh <YOUR_TOKEN>"
    echo "您可以在 Cloudflare Zero Trust Dashboard -> Networks -> Tunnels 中获取 Token。"
    exit 1
fi

echo "正在使用 Token 启动 Cloudflare Tunnel..."
./tools/cloudflared tunnel run --token $1

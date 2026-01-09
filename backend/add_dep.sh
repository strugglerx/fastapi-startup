#!/bin/bash

# 自动添加依赖包到 requirements.txt（自动获取版本号）

if [ $# -eq 0 ]; then
    echo "用法: $0 <包名1> <包名2> ..."
    echo "示例: $0 python-multipart"
    echo "示例: $0 fastapi uvicorn python-multipart"
    exit 1
fi

for package in "$@"; do
    echo "📦 处理包: $package"
    
    # 安装包（如果已存在也会更新到最新）
    pip install "$package"
    
    # 获取版本号
    version=$(pip show "$package" 2>/dev/null | grep Version | awk '{print $2}')
    
    if [ -z "$version" ]; then
        echo "❌ 错误: 包 $package 安装失败或不存在"
        continue
    fi
    
    # 确保 requirements.txt 存在
    touch requirements.txt
    
    # 删除已存在的该包行（避免重复）
    if grep -q "^$package==" requirements.txt; then
        sed -i.tmp "/^$package==/d" requirements.txt
        echo "🔄 更新包: $package==$version"
    else
        echo "✅ 添加包: $package==$version"
    fi
    
    # 确保文件以换行结尾
    if [ -s requirements.txt ] && [ "$(tail -c1 requirements.txt)" != "" ]; then
        echo "" >> requirements.txt
    fi
    
    # 添加包和版本号
    echo "$package==$version" >> requirements.txt
    
    # 清理临时文件
    rm -f requirements.txt.tmp
done

echo ""
echo "📋 更新后的 requirements.txt:"
cat requirements.txt
#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================"
echo "AI分析功能环境配置工具"
echo "================================"
echo

# 检查是否已存在.env文件
if [ -f .env ]; then
    echo -e "${YELLOW}[警告] .env文件已存在${NC}"
    echo
    read -p "是否覆盖现有配置？(y/n): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "操作已取消"
        exit 0
    fi
fi

echo
echo "请按照以下步骤操作："
echo
echo "1. 访问 https://platform.deepseek.com/"
echo "2. 注册/登录账号"
echo "3. 进入API Keys页面"
echo "4. 创建并复制API密钥"
echo
read -p "请输入您的 DeepSeek API Key: " api_key

if [ -z "$api_key" ]; then
    echo -e "${RED}[错误] API Key不能为空${NC}"
    exit 1
fi

# 创建.env文件
cat > .env << EOF
# DeepSeek AI配置
# 获取地址：https://platform.deepseek.com/
DEEPSEEK_API_KEY=$api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
EOF

echo
echo "================================"
echo -e "${GREEN}[成功] 配置文件已创建！${NC}"
echo "================================"
echo
echo "文件位置: $(pwd)/.env"
echo
echo "下一步："
echo "1. 安装依赖: pip install -r requirements.txt"
echo "2. 运行程序: streamlit run app.py"
echo


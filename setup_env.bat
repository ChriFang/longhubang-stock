@echo off
chcp 65001 > nul
echo ================================
echo AI分析功能环境配置工具
echo ================================
echo.

REM 检查是否已存在.env文件
if exist .env (
    echo [警告] .env文件已存在
    echo.
    set /p "overwrite=是否覆盖现有配置？(y/n): "
    if /i not "%overwrite%"=="y" (
        echo 操作已取消
        pause
        exit /b
    )
)

echo.
echo 请按照以下步骤操作：
echo.
echo 1. 访问 https://open.bigmodel.cn/
echo 2. 注册/登录账号
echo 3. 进入"API密钥"页面
echo 4. 创建并复制API密钥
echo.
set /p "api_key=请输入您的智谱AI API Key: "

if "%api_key%"=="" (
    echo [错误] API Key不能为空
    pause
    exit /b
)

REM 创建.env文件
(
echo # 智谱清言AI配置
echo # 获取地址：https://open.bigmodel.cn/
echo ZHIPU_API_KEY=%api_key%
) > .env

echo.
echo ================================
echo [成功] 配置文件已创建！
echo ================================
echo.
echo 文件位置: %cd%\.env
echo.
echo 下一步：
echo 1. 安装依赖: pip install -r requirements.txt
echo 2. 运行程序: streamlit run app.py
echo.
pause


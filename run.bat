@echo off
echo 启动游资龙虎榜分析系统...

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo 正在创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖包
if not exist "venv\Lib\site-packages\streamlit" (
    echo 正在安装依赖包...
    pip install -r requirements.txt
)

REM 启动应用
echo 启动Streamlit应用...
streamlit run app.py

pause
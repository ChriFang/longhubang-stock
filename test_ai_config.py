"""
测试AI配置是否正确
"""

import sys
import os

def test_env_file():
    """测试.env文件是否存在"""
    print("1. 检查.env文件...")
    if os.path.exists('.env'):
        print("   ✓ .env文件存在")
        return True
    else:
        print("   ✗ .env文件不存在")
        print("   请运行 setup_env.bat (Windows) 或 ./setup_env.sh (Linux/Mac)")
        return False

def test_dotenv_package():
    """测试python-dotenv是否安装"""
    print("\n2. 检查python-dotenv包...")
    try:
        import dotenv
        print("   ✓ python-dotenv已安装")
        return True
    except ImportError:
        print("   ✗ python-dotenv未安装")
        print("   请运行: pip install python-dotenv")
        return False

def test_zhipuai_package():
    """测试zhipuai是否安装"""
    print("\n3. 检查zhipuai包...")
    try:
        import zhipuai
        print("   ✓ zhipuai已安装")
        return True
    except ImportError:
        print("   ✗ zhipuai未安装")
        print("   请运行: pip install zhipuai")
        return False

def test_api_key():
    """测试API Key是否配置"""
    print("\n4. 检查API Key配置...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('ZHIPU_API_KEY')
        if api_key and api_key != 'your_api_key_here':
            print(f"   ✓ API Key已配置: {api_key[:10]}...")
            return True
        else:
            print("   ✗ API Key未正确配置")
            print("   请在.env文件中设置有效的ZHIPU_API_KEY")
            return False
    except Exception as e:
        print(f"   ✗ 配置检查失败: {e}")
        return False

def test_ai_analyzer():
    """测试AI分析器是否能初始化"""
    print("\n5. 测试AI分析器初始化...")
    try:
        from ai_analyzer import AILongHuAnalyzer
        analyzer = AILongHuAnalyzer()
        print("   ✓ AI分析器初始化成功")
        return True
    except ValueError as e:
        print(f"   ✗ AI分析器初始化失败: {e}")
        return False
    except Exception as e:
        print(f"   ✗ 发生错误: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("AI分析功能配置测试")
    print("=" * 50)
    
    results = []
    results.append(test_env_file())
    results.append(test_dotenv_package())
    results.append(test_zhipuai_package())
    
    if all(results):
        results.append(test_api_key())
        if results[-1]:
            results.append(test_ai_analyzer())
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✓ 所有测试通过 ({passed}/{total})")
        print("\n恭喜！AI分析功能已正确配置，可以使用了！")
        print("运行 'streamlit run app.py' 启动应用")
    else:
        print(f"✗ 部分测试失败 ({passed}/{total})")
        print("\n请根据上述提示完成配置")
    
    print("=" * 50)
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


"""
测试 GitHub Copilot API 是否可用
"""
from openai import OpenAI
from config import Config

def test_github_copilot():
    """测试 DeepSeek API"""
    
    print("=" * 60)
    print("🧪 测试 DeepSeek API")
    print("=" * 60)
    print(f"📍 Base URL: {Config.OPENAI_BASE_URL}")
    print(f"🔑 API Key: {Config.OPENAI_API_KEY[:20]}...")
    print(f"🤖 Model: {Config.OPENAI_MODEL}")
    print("-" * 60)
    
    try:
        # 创建客户端
        client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            default_headers={
                "Editor-Version": "vscode/1.85.0",
                "Editor-Plugin-Version": "copilot/1.150.0",
                "User-Agent": "GithubCopilot/1.150.0"
            }
        )
        
        # print("✅ 客户端创建成功")
        
        # # 测试普通请求
        # print("\n📤 发送测试请求（普通模式）...")
        # response = client.chat.completions.create(
        #     model=Config.OPENAI_MODEL,
        #     messages=[
        #         {"role": "system", "content": "你是一个编程助手。"},
        #         {"role": "user", "content": "说一句话测试"}
        #     ],
        #     max_tokens=50
        # )
        
        # print(f"✅ 普通请求成功！")
        # print(f"📥 回复: {response.choices[0].message.content}")
        
        # 测试流式请求
        print("\n📤 发送测试请求（流式模式）...")
        stream = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个编程助手。"},
                {"role": "user", "content": "数到5"}
            ],
            max_tokens=50,
            stream=True
        )
        
        print(f"✅ 流式请求启动！")
        print(f"📥 流式回复: ", end="", flush=True)
        
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    print(delta.content, end="", flush=True)
        
        print("\n✅ 流式请求成功！")
        print("=" * 60)
        print("🎉 GitHub Copilot API 完全可用！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        print("💡 建议：")
        print("1. 检查 API Key 是否正确")
        print("2. 确认是否有 GitHub Copilot 订阅")
        print("3. 尝试使用其他 Base URL")
        print("=" * 60)

if __name__ == '__main__':
    test_github_copilot()
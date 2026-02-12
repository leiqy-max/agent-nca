import os
import yaml
import sys

# 1. 模拟 main.py 的加载逻辑
print("Loading config.yaml...")
if os.path.exists("backend/config.yaml"):
    with open("backend/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        if config:
            if "llm" in config:
                llm = config["llm"]
                print(f"Config LLM: {llm}")
                if "provider" in llm: os.environ["LLM_PROVIDER"] = str(llm["provider"])
                if "api_key" in llm: os.environ["LLM_API_KEY"] = str(llm["api_key"])
                if "embedding_model" in llm: os.environ["EMBEDDING_MODEL"] = str(llm["embedding_model"])

print(f"Env LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
print(f"Env EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL')}")

# 2. 测试 Factory
sys.path.append(os.path.join(os.getcwd(), "backend"))
try:
    from llm.factory import get_embedding_client
    client = get_embedding_client()
    print(f"Client Type: {type(client)}")
    print(f"Client Model: {client.model}")
    
    # 3. 生成 Embedding
    vec = client.embed_text("test")
    print(f"Vector Dimension: {len(vec)}")
except Exception as e:
    print(f"Error: {e}")

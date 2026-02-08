from llm.embedding import embed_text

if __name__ == "__main__":
    text = "这是一个用于测试运维知识向量化的示例文本"
    vec = embed_text(text)

    print("向量类型:", type(vec))
    print("向量长度:", len(vec))
    print("前5个值:", vec[:5])

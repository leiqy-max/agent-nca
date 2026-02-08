
import os
from sqlalchemy import text
from db import engine
from llm.embedding import embed_text

def debug_retrieve(query: str, top_k: int = 3):
    print(f"\n--- Debugging Query: {query} ---")
    query_embedding = embed_text(query)

    with engine.connect() as connection:
        # 修改 SQL 以返回距离
        result = connection.execute(
            text("""
            SELECT content, metadata, embedding <-> (:query_embedding)::vector AS distance
            FROM documents
            ORDER BY distance ASC
            LIMIT :top_k;
            """),
            {
                "query_embedding": query_embedding,
                "top_k": top_k
            }
        )
        
        rows = result.fetchall()
        if not rows:
            print("No documents found.")
            return

        for i, row in enumerate(rows):
            print(f"Doc {i+1}: Distance = {row[2]:.4f}")
            print(f"Content Preview: {row[0][:50]}...")

if __name__ == "__main__":
    # 需要设置 API Key 才能运行
    if not os.getenv("ZHIPUAI_API_KEY"):
        print("Please set ZHIPUAI_API_KEY environment variable.")
    else:
        debug_retrieve("系统A无法登录")
        debug_retrieve("在吗")
        debug_retrieve("今天天气怎么样")

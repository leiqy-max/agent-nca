
import sys
import os

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.retriever import retrieve_similar_documents

def test_retrieval():
    query = "规划天线经纬度和铁塔经纬度误差在多少米校验"
    print(f"Testing retrieval for query: {query}")
    
    results = retrieve_similar_documents(query, top_k=5)
    
    if not results:
        print("No results found.")
        return

    print(f"\nFound {len(results)} results:")
    for i, row in enumerate(results):
        content = row[0]
        metadata = row[1]
        distance = row[2]
        print(f"\n--- Result {i+1} (Distance: {distance:.4f}) ---")
        print(f"Metadata: {metadata}")
        print(f"Content Preview: {content[:100]}...")
        if "天线" in content and "50" in content:
             print(">>> MATCH FOUND IN CONTENT <<<")

if __name__ == "__main__":
    test_retrieval()

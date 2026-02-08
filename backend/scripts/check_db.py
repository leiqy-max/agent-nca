
import sys
import os
from sqlalchemy import text

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import engine

def check_db_for_file():
    filename = "147-无线天面的模型及流程优化20250710.docx"
    print(f"Checking DB for file: {filename}")
    
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT count(*), content FROM documents WHERE metadata->>'filename' = :filename GROUP BY content LIMIT 1"),
            {"filename": filename}
        ).fetchall()
        
        if not result:
            print("File NOT found in database.")
        else:
            print(f"File found in database with chunks.")
            print(f"Sample chunk: {result[0][1][:100]}...")

if __name__ == "__main__":
    check_db_for_file()

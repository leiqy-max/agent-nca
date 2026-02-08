import os
import sys
import glob

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag.loader import load_document

def ingest_directory(directory_path: str):
    """
    Ingest all supported files from a directory into the vector database.
    """
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        return

    # Supported extensions (expandable)
    patterns = ["*.txt", "*.md", "*.log", "*.docx"]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory_path, "**", pattern), recursive=True))

    print(f"Found {len(files)} files to ingest.")

    for file_path in files:
        print(f"Processing: {file_path}")
        try:
            metadata = {
                "source": file_path,
                "filename": os.path.basename(file_path)
            }
            load_document(file_path, metadata)
            print(f"Successfully loaded: {file_path}")
        except Exception as e:
            print(f"Failed to load {file_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_local.py <directory_path>")
    else:
        target_dir = sys.argv[1]
        ingest_directory(target_dir)

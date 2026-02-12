import sys
import os

print("Validating imports...")
try:
    import fastapi
    import uvicorn
    import sqlalchemy
    import pgvector
    import captcha
    import jinja2
    import docx
    import openpyxl
    import pandas
    # Add backend to path to check internal modules
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    import main
    print("Imports OK.")
    sys.exit(0)
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

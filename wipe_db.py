import shutil
import os

db_path = "./db"
if os.path.exists(db_path):
    print(f"Purging vector database at {db_path}...")
    shutil.rmtree(db_path)
    print("Database wiped. Re-ingest documents to apply new security levels.")
else:
    print("Database directory not found. Already clean.")

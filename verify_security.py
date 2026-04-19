from brain import SecureRAG
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

rag = SecureRAG()

# 1. Create a dummy test file
test_file = "security_test.txt"
with open(test_file, "w") as f:
    f.write("CONFIDENTIAL ADMIN DATA: The CEO salary is $850,000. Access Level: Admin.\n")
    f.write("GENERAL EMPLOYEE DATA: The office is open from 9 to 5. Public Info.\n")

# 2. Manual ingestion to test logic without PDF overhead
print("Ingesting test data...")
loader = TextLoader(test_file)
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

for chunk in chunks:
    role = rag.auto_classify(chunk.page_content)
    level = rag.ROLE_LEVELS.get(role, 1)
    chunk.metadata["allowed_role"] = role
    chunk.metadata["clearance_level"] = level
    chunk.metadata["source"] = test_file

rag.vector_db.add_documents(chunks)

# 3. Test Queries
print("\n--- Testing as Employee (Level 1) ---")
# Employee query for Admin data
res_emp = rag.query("What is the CEO salary?", "employee")
print(f"Answer: {res_emp['answer']}")
print(f"Sources Count: {len(res_emp['sources'])}")

print("\n--- Testing as Admin (Level 3) ---")
res_adm = rag.query("What is the CEO salary?", "admin")
print(f"Answer: {res_adm['answer']}")
print(f"Sources Count: {len(res_adm['sources'])}")

# Clean up
if os.path.exists(test_file): os.remove(test_file)

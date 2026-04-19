from brain import SecureRAG

rag = SecureRAG()
# Access the underlying collection
collection = rag.vector_db._collection

# Fetch all data
data = collection.get()

print(f"Total Chunks in DB: {len(data['ids'])}")
print("-" * 50)

for i in range(len(data['ids'])):
    chunk_id = data['ids'][i]
    metadata = data['metadatas'][i]
    content = data['documents'][i]
    
    # We are specifically looking for the salary leak
    if "salary" in content.lower() or "1,000,000" in content or "850,000" in content:
        print(f"ID: {chunk_id}")
        print(f"ROLE: {metadata.get('allowed_role')} | LEVEL: {metadata.get('clearance_level')}")
        print(f"FILE: {metadata.get('source')}")
        print(f"CONTENT: {content[:100]}...")
        print("-" * 30)

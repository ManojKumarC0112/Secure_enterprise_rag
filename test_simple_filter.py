from brain import SecureRAG

rag = SecureRAG()
query = "CEO base salary"

print("--- Testing Simple Equality Filter (allowed_role == 'employee') ---")
docs = rag.vector_db.similarity_search(
    query, 
    k=3, 
    filter={"allowed_role": "employee"}
)
print(f"Docs found: {len(docs)}")
for d in docs:
    print(f"Role: {d.metadata.get('allowed_role')} | Content: {d.page_content[:50]}...")

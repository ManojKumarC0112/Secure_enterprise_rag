from brain import SecureRAG

rag = SecureRAG()
query = "CEO base salary"

print("--- Testing Employee Access (should be empty/denied) ---")
# Manually run the code from brain.py's query method
accessible_roles = ["employee"]
docs = rag.vector_db.similarity_search(
    query, 
    k=3, 
    filter={"allowed_role": {"$in": accessible_roles}}
)
print(f"Employee docs found: {len(docs)}")
for d in docs:
    print(f"Role: {d.metadata.get('allowed_role')} | Content: {d.page_content[:50]}...")

print("\n--- Testing Admin Access (should contain salary) ---")
accessible_roles = ["admin", "manager", "employee"]
docs = rag.vector_db.similarity_search(
    query, 
    k=3, 
    filter={"allowed_role": {"$in": accessible_roles}}
)
print(f"Admin docs found: {len(docs)}")
for d in docs:
    print(f"Role: {d.metadata.get('allowed_role')} | Content: {d.page_content[:50]}...")

from brain import SecureRAG

rag = SecureRAG()
query = "what is the ceo base salary"
role = "employee"

# 1. Check numerical level
user_clearance = rag.ROLE_LEVELS.get(role, 1)
print(f"User Role: {role} | Level: {user_clearance}")

# 2. Perform search
docs = rag.vector_db.similarity_search(
    query, 
    k=3, 
    filter={"clearance_level": {"$lte": user_clearance}}
)

print(f"Docs found: {len(docs)}")
for i, d in enumerate(docs):
    print(f"DOC {i+1}:")
    print(f"  Source: {d.metadata.get('source')}")
    print(f"  Level in Metadata: {d.metadata.get('clearance_level')}")
    print(f"  Content: {d.page_content[:100]}...")

from brain import SecureRAG

rag = SecureRAG()
query = "CEO Base Salary"
results = rag.vector_db.similarity_search_with_score(query, k=1)

print(f"Top Result for: '{query}'")
for i, (doc, score) in enumerate(results):
    print(f"\n--- Result {i+1} (Score: {score:.4f}) ---")
    print(f"Role: {doc.metadata.get('allowed_role')}")
    print(f"Content: {doc.page_content[:200]}") # Only first 200 chars to avoid truncation

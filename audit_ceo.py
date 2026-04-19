from brain import SecureRAG

rag = SecureRAG()
query = "$850,000"
results = rag.vector_db.similarity_search_with_score(query, k=2)

print(f"Top 2 Results for: '{query}'")
for i, (doc, score) in enumerate(results):
    print(f"\n--- Result {i+1} (Score: {score:.4f}) ---")
    print(f"Role: {doc.metadata.get('allowed_role')}")
    print(f"Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")

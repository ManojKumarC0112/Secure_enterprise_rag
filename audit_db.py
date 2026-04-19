from brain import SecureRAG

rag = SecureRAG()
query = "CEO base salary"
# Search across ALL roles to see what role is currently assigned to these chunks
results = rag.vector_db.similarity_search_with_score(query, k=5)

print(f"Audit for query: '{query}'")
for i, (doc, score) in enumerate(results):
    print(f"\n--- Result {i+1} (Score: {score:.4f}) ---")
    print(f"Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")

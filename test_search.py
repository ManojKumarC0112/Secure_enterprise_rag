from brain import SecureRAG

rag = SecureRAG()
# We bypass the LLM and just do the search part directly to prove filtering
print("--- Employee Search for Salary ---")
employee_docs = rag.vector_db.similarity_search("What are the salaries for L4?", k=3, filter={"allowed_role": {"$in": ["employee"]}})
if not employee_docs:
    print("Access Denied: You do not have permissions.")
else:
    for doc in employee_docs:
        print("Employee sees:", doc.metadata)

print("\n--- Admin Search for Salary ---")
admin_docs = rag.vector_db.similarity_search("What are the salaries for L4?", k=3, filter={"allowed_role": {"$in": ["admin", "manager", "employee"]}})
if not admin_docs:
    print("Access Denied: You do not have permissions.")
else:
    for doc in admin_docs:
        print("Admin sees:", doc.metadata)

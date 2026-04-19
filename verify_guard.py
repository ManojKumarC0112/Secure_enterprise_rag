from brain import SecureRAG

rag = SecureRAG()

# 1. Test as Employee asking about 'salary' (Admin keyword in JSON)
print("--- Testing Employee Access to 'Salary' ---")
res = rag.query("What is the ceo base salary?", "employee")
print(f"Answer: {res['answer']}")
print(f"Sources: {len(res['sources'])}")

# Check if it was blocked by the Guard
if "Security Alert" in res['answer'] or "Access to sensitive" in res['answer']:
    print("\n✅ SUCCESS: Zero-Hallucination Guard blocked the query before AI call.")
else:
    print("\n❌ FAILURE: Query was passed to the AI.")

# 2. Test as Admin asking about 'salary' (Should proceed)
print("\n--- Testing Admin Access to 'Salary' ---")
res_admin = rag.query("What is the ceo base salary?", "admin")
print(f"Answer: {res_admin['answer']}")
print(f"Docs Found: {len(res_admin['sources'])}")

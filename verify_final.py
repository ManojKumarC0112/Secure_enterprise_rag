from brain import SecureRAG
import json

# 1. Add a regex pattern to the Admin policy in JSON
policy_path = "security_policies.json"
with open(policy_path, "r") as f:
    policies = json.load(f)

# Pattern for a secret ID format: ACME-SEC-XXXX
SECRET_PATTERN = "ACME-SEC-[0-9]{4}"
if SECRET_PATTERN not in policies["admin"]["patterns"]:
    policies["admin"]["patterns"].append(SECRET_PATTERN)

with open(policy_path, "w") as f:
    json.dump(policies, f, indent=2)

print(f"Added pattern '{SECRET_PATTERN}' to Admin Policies.")

# 2. Initialize Brain
rag = SecureRAG()

# 3. Test as Employee with a query matching the pattern
query = "Tell me about record ACME-SEC-9912"
print(f"\nQuery: '{query}'")
res = rag.query(query, "employee")

print(f"Answer: {res['answer']}")

if "pattern detected" in res['answer']:
    print("\n✅ SUCCESS: Zero-Hallucination Guard blocked a dynamic regex pattern!")
else:
    print("\n❌ FAILURE: Regex pattern was ignored.")

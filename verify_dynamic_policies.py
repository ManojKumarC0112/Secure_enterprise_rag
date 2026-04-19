from brain import SecureRAG
import json
import os

# 1. Update the security_policies.json with a custom 'Secret' codename
policy_path = "security_policies.json"
with open(policy_path, "r") as f:
    policies = json.load(f)

# Add a unique project codename to Admin keywords
CODENAME = "PROJECT_VOID_WALKER"
if CODENAME not in policies["admin"]["keywords"]:
    policies["admin"]["keywords"].append(CODENAME)

with open(policy_path, "w") as f:
    json.dump(policies, f, indent=2)

print(f"Added '{CODENAME}' to Admin Security Policies.")

# 2. Initialize Brain (it should load the new JSON)
rag = SecureRAG()

# 3. Test Classification
test_text = f"This document discusses the deployment of {CODENAME} in the Q4 quadrant."
detected_role = rag.auto_classify(test_text)

print(f"\nTest Text: '{test_text}'")
print(f"Detected Role: {detected_role.upper()}")

if detected_role == "admin":
    print("\n✅ SUCCESS: Dynamic Policy Engine correctly identified the secret codename.")
else:
    print("\n❌ FAILURE: Policy Engine did not detect the keyword.")

# No cleanup of CODENAME needed, good for the user to keep as an example

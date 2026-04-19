from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

import re
import warnings
import json
import os
warnings.filterwarnings('ignore')

class SecureRAG:
    def __init__(self):
        # 1. Load the same embedding model used in Phase 1
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # 2. Connect to the existing vector database
        self.vector_db = Chroma(
            persist_directory="./db", 
            embedding_function=self.embeddings
        )
        
        # 3. Initialize local SLM via Ollama
        self.llm = Ollama(model="qwen2:0.5b")

        # Map roles to strictly numerical clearance levels for robust filtering
        self.ROLE_LEVELS = {
            "admin": 3,
            "manager": 2,
            "employee": 1
        }
        
        # Load Dynamic Security Policies
        self.policies = self.load_policies()

    def load_policies(self):
        policy_path = "security_policies.json"
        if os.path.exists(policy_path):
            try:
                with open(policy_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading security policies: {e}")
        return {"admin": {"keywords": [], "patterns": []}, "manager": {"keywords": [], "patterns": []}}

    def query(self, user_query: str, user_role: str, chat_history: list = None):
        if chat_history is None:
            chat_history = []
            
        # Get numerical clearance level (default to 1 if unknown)
        user_clearance = self.ROLE_LEVELS.get(user_role, 1)

        # 4. Search with Metadata Filtering using $lte (Less Than or Equal)
        # This ensures an Employee (1) NEVER sees Manager (2) or Admin (3) records.
        # This syntax is highly robust across Chroma versions.
        docs = self.vector_db.similarity_search(
            user_query, 
            k=3, 
            filter={"clearance_level": {"$lte": user_clearance}}
        )

        if not docs:
            return {
                "answer": "I do not have clearance to access information relevant to this query, or no relevant public documents exist.",
                "sources": []
            }

        # Format chat history into string
        history_context = ""
        if chat_history:
            history_context = "Previous Conversation:\n"
            for msg in chat_history:
                role_label = "User" if msg.get("role") == "user" else "Assistant"
                history_context += f"{role_label}: {msg.get('content')}\n"

        # 5. Build the Context and Ask LLM
        context = "\n".join([doc.page_content for doc in docs])
        prompt = f"""You are a helpful and secure AI assistant.
Answer the question based strictly on the provided Context.
If the context does not contain the answer, say "I do not have clearance to access this information."

Context:
{context}

{history_context}

Question: {user_query}

Short, direct answer:"""
        
        answer = self.llm.invoke(prompt)
        
        # Package explainable AI sources
        source_data = []
        for d in docs:
            source_data.append({
                "source": d.metadata.get("source", "Unknown"),
                "text": d.page_content
            })
            
        return {
            "answer": answer,
            "sources": source_data
        }

    def auto_classify(self, sample_text: str) -> str:
        # --- DYNAMIC POLICY BOOSTER (Security Flex) ---
        text_lower = sample_text.lower()
        
        # 1. Check Admin Policies
        admin_cfg = self.policies.get("admin", {})
        for kw in admin_cfg.get("keywords", []):
            if kw.lower() in text_lower: return "admin"
        for pattern in admin_cfg.get("patterns", []):
            if re.search(pattern, sample_text): return "admin"

        # 2. Check Manager Policies
        manager_cfg = self.policies.get("manager", {})
        for kw in manager_cfg.get("keywords", []):
            if kw.lower() in text_lower: return "manager"
        for pattern in manager_cfg.get("patterns", []):
            if re.search(pattern, sample_text): return "manager"
            
        # 3. Fallback to SLM for ambiguous analysis
        prompt = f"""
        You are a highly secure document classification AI. Read the target document snippet below.
        You must reply with EXACTLY ONE WORD determining its security clearance level: 
        Reply "employee" if it is general company info, handbooks, tech docs, or public HR policies.
        Reply "manager" if it contains project roadmaps, team strategies, or standard quarterly plans.
        Reply "admin" if it contains strictly confidential financial records, executive salaries, M&A details, or passwords.

        Document Snippet:
        {sample_text}

        Reply with exactly one word (employee, manager, or admin):"""
        
        # Invoke the LLM
        response = self.llm.invoke(prompt).strip().lower()
        
        if "admin" in response:
            return "admin"
        elif "manager" in response:
            return "manager"
        else:
            return "employee"

    def sanitize_pii(self, text: str) -> str:
        """Automatically redacts sensitive SSNs and Credit Cards before ingestion."""
        # Redact SSNs (XXX-XX-XXXX)
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
        # Redact Credit Cards (XXXX-XXXX-XXXX-XXXX)
        text = re.sub(r'\b(?:\d{4}-){3}\d{4}\b|\b\d{16}\b', '[REDACTED_CC]', text)
        # Standard Phone numbers
        text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[REDACTED_PHONE]', text)
        return text

    def ingest_document(self, file_path: str, role: str):
        """Dynamically ingests a new PDF into the active ChromaDB instance."""
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        
        assigned_roles = set()
        for chunk in chunks:
            chunk.page_content = self.sanitize_pii(chunk.page_content)
            
            chunk_role = role
            if role == "auto":
                chunk_role = self.auto_classify(chunk.page_content)
            
            # Map role to level for storage
            level = self.ROLE_LEVELS.get(chunk_role, 1)
            
            chunk.metadata["allowed_role"] = chunk_role
            chunk.metadata["clearance_level"] = level
            chunk.metadata["source"] = file_path
            assigned_roles.add(chunk_role)
        
        self.vector_db.add_documents(chunks)
        
        if hasattr(self.vector_db, "persist"):
            self.vector_db.persist()
            
        if "admin" in assigned_roles: return "admin"
        if "manager" in assigned_roles: return "manager"
        return "employee"

# Quick Test Script
if __name__ == "__main__":
    rag = SecureRAG()
    # Test as a Developer/Employee
    print("--- Testing as Employee ---")
    print(rag.query("What are the salaries for L4?", "employee")["answer"]) 
    
    print("\n--- Testing as Admin ---")
    print(rag.query("What are the salaries for L4?", "admin")["answer"])

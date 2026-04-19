from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

import warnings
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

    def query(self, user_query: str, user_role: str, chat_history: list = None):
        if chat_history is None:
            chat_history = []
            
        # Define hierarchical access logic
        # Admin sees everything; Manager sees manager + employee; Employee sees employee.
        accessible_roles = ["employee"]
        if user_role == "admin":
            accessible_roles = ["admin", "manager", "employee"]
        elif user_role == "manager":
            accessible_roles = ["manager", "employee"]

        # 4. Search with Metadata Filtering
        # This ensures the LLM NEVER even sees chunks the user isn't allowed to see.
        docs = self.vector_db.similarity_search(
            user_query, 
            k=3, 
            filter={"allowed_role": {"$in": accessible_roles}}
        )

        if not docs:
            return "Access Denied: You do not have permissions to view the documents required to answer this or no relevant documents exist."

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
        
        return self.llm.invoke(prompt)

    def auto_classify(self, sample_text: str) -> str:
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
        
        # Filter strict output
        if "admin" in response:
            return "admin"
        elif "manager" in response:
            return "manager"
        else:
            return "employee" # Least privilege default fallback

    def ingest_document(self, file_path: str, role: str):
        """Dynamically ingests a new PDF into the active ChromaDB instance."""
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        
        assigned_roles = set()
        for chunk in chunks:
            chunk_role = role
            if role == "auto":
                # Auto-classify the individual chunk to guarantee true Zero-Trust granularity
                chunk_role = self.auto_classify(chunk.page_content[:1000])
            
            chunk.metadata["allowed_role"] = chunk_role
            chunk.metadata["source"] = file_path
            assigned_roles.add(chunk_role)
        
        self.vector_db.add_documents(chunks)
        
        # For chromadb > 1.5, persistence is automatic. If older, we would call self.vector_db.persist()
        if hasattr(self.vector_db, "persist"):
            self.vector_db.persist()
            
        if len(assigned_roles) > 1:
            return "mixed_clearance"
        elif len(assigned_roles) == 1:
            return list(assigned_roles)[0]
        else:
            return "employee"

# Quick Test Script
if __name__ == "__main__":
    rag = SecureRAG()
    # Test as a Developer/Employee
    print("--- Testing as Employee ---")
    print(rag.query("What are the salaries for L4?", "employee")) 
    
    print("\n--- Testing as Admin ---")
    print(rag.query("What are the salaries for L4?", "admin"))

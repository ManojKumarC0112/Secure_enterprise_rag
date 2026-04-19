import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 1. Initialize Embeddings (Runs locally on your CPU/GPU)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def ingest_docs():
    # Define our files and their security levels
    files = [
        {"path": "data/public_handbook.pdf", "role": "employee"},
        {"path": "data/product_roadmap.pdf", "role": "manager"},
        {"path": "data/salary_structure.pdf", "role": "admin"}
    ]
    
    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    for file in files:
        loader = PyPDFLoader(file["path"])
        docs = loader.load()
        
        # Add the security tag to metadata before splitting
        for doc in docs:
            doc.metadata["allowed_role"] = file["role"]
            doc.metadata["source"] = file["path"]

        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)

    # 2. Create the Vector DB and save it locally in /db folder
    vector_db = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory="./db"
    )
    print("✅ Ingestion Complete: Documents tagged and stored.")

if __name__ == "__main__":
    ingest_docs()

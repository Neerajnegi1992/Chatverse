import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
#import chromadb
load_dotenv()

key  =  os.getenv("GOOGLE_API_KEY")
# Creating Chunks Embedding
embedding_model = GoogleGenerativeAIEmbeddings(google_api_key=key, model="models/embedding-001")

def save_pdf_embed(pdf_file_list):
    # Load and embed the documents with metadata
    documents = [
    {"file_path": "D001026163_Rev_E_Planned_Maintenance_Level_1_Zenition_50_70.pdf", "metadata": {"product": "Zenition 50/70", "manual_type": "Planned maintenance"}},
    {"file_path": "DMR244663_zen0.pdf", "metadata": {"product": "Zenition 70", "manual_type": "Repair"}}
    ]   
    # Load documents and add embeddings
    docs_with_embeddings = []
    for doc in documents:
        loader = PyPDFLoader(doc["file_path"])

        loaded_docs = loader.load()

        # Ensure text is a single string
        # Extract text content from each Document object
        text = "\n".join([d.page_content for d in loaded_docs])
        print("text type",type(text))
        #print("text",text)
        document = Document(page_content=text, metadata=doc["metadata"])
        docs_with_embeddings.append(document)


    # Store embeddings in FAISS vector store
    vector_store = FAISS.from_documents(docs_with_embeddings,embedding=embedding_model)
    vector_store.save_local("faiss_index_new")

def get_retriever():
    retriever = FAISS.load_local("faiss_index_new", embedding_model,allow_dangerous_deserialization=True)
    return retriever

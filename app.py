import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
from langchain.prompts import PromptTemplate
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Streamlit UI ---
st.set_page_config(page_title="RAG Chatbot", layout="wide")
st.title("💬 RAG Chatbot with Groq + Chroma")

# API Key check
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is not set. Please set it in your environment variables.")
    st.stop()

# Initialize components
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

vector_store = Chroma(
    collection_name="rag_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)

# Prompt template
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a factual assistant. Use only the context to answer.
Context:
{context}

Question: {question}
Answer:"""
)

# Initialize LLM
llm = ChatGroq(
    model_name="llama3-8b-8192",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)

# --- File Handling Functions ---
def load_file(file):
    """Load text from either PDF or TXT file"""
    try:
        if file.name.endswith(".txt"):
            return file.read().decode("utf-8")
        elif file.name.endswith(".pdf"):
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        return ""
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return ""

def process_text(text):
    """Split text into chunks and create documents"""
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
        # Create initial document
        doc = Document(page_content=text)
        # Split into chunks
        chunks = splitter.split_documents([doc])
        return chunks
    except Exception as e:
        st.error(f"Error processing text: {str(e)}")
        return []

# --- Streamlit UI Components ---
uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf"])

if st.button("Index Document"):
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            text = load_file(uploaded_file)
            if text:
                chunks = process_text(text)
                if chunks:
                    vector_store.add_documents(documents=chunks)
                    count = len(chunks)
                    st.success(f"Indexed {count} chunks successfully!")
                else:
                    st.error("No valid chunks were created from the document.")
            else:
                st.error("The uploaded file appears to be empty.")
    else:
        st.error("Please upload a file before indexing.")

# Query handling
query = st.text_input("Ask something about your documents:")

if st.button('Ask Question'):
    if query:
        if len(vector_store.get()['documents']) > 0:  # Check if documents exist
            with st.spinner("Searching knowledge base..."):
                retriever = vector_store.as_retriever(search_kwargs={"k": 3})
                docs = retriever.get_relevant_documents(query)
                context = "\n\n".join([d.page_content for d in docs])
                final_prompt = prompt.format(context=context, question=query)

            with st.spinner("Generating answer..."):
                try:
                    answer = llm.invoke(final_prompt)
                    st.subheader("Answer")
                    st.write(answer.content)
                except Exception as e:
                    st.error(f"Error generating answer: {str(e)}")
        else:
            st.error("Please index documents before asking questions.")
    else:
        st.warning("Please enter a question.")
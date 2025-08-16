# 💬 RAG Chatbot (Groq + Chroma + Streamlit)

**Summary:**  
This project is a complete **Q/A chatbot** built with the **RAG (Retrieval-Augmented Generation)** approach.  
It’s a simple web app where you can upload your documents and then ask questions about them.  
The chatbot looks through your document, picks out the most relevant parts, and uses them as context to answer your question.  
Your question and the selected context are combined into a prompt and sent to the LLM, which then gives back a clear, accurate, and well-formatted answer based only on your document.  

This is a simple **Retrieval-Augmented Generation (RAG) chatbot** built with:

- **Groq LLMs** for fast and efficient text generation  
- **HuggingFace embeddings** for semantic vectorization  
- **Chroma** as the vector database  
- **Streamlit** for the frontend  

You can upload your own documents (`PDF` or `TXT`), index them into a local Chroma database, and then ask questions.  
The chatbot retrieves relevant chunks from your docs and uses Groq’s model to generate fact-based answers.  

---

## ✨ Features
- 📄 Upload `.pdf` or `.txt` files  
- 🔍 Automatically splits docs into chunks and stores them in Chroma DB  
- 💡 Ask natural questions about your documents  
- ✅ Answers grounded in your data (no random hallucinations)  
- 🖥️ Clean Streamlit web interface  

---

## 📂 Project Layout
```
├── app.py             # Main Streamlit app
├── chroma_db/         # Chroma vector store (created after indexing)
├── .env               # Stores API key
├── requirements.txt   # Dependencies
└── README.md  
```

---

## ⚡ Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/rag-chatbot.git
cd rag-chatbot
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate    # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API key
Create a `.env` file in the project root and add your Groq API key:
```ini
GROQ_API_KEY=your_api_key_here
```

### 5. Run the app
```bash
streamlit run app.py
```

---

## 🖥️ How to Use
1. Start the app  
2. Upload a PDF or TXT file  
3. Click **“Index Document”** (stores chunks in ChromaDB)  
4. Type a question in the input box  
5. Get answers based only on your document  

---

## 🧰 Requirements
All dependencies are listed in `requirements.txt`:

```
streamlit
langchain
langchain-core
langchain-chroma
langchain-huggingface
langchain-groq
PyPDF2
python-dotenv
```

---

## ⚙️ Tech Details
- **Embeddings**: `sentence-transformers/all-mpnet-base-v2`  
- **Vector DB**: Chroma with DuckDB backend (saved in `./chroma_db`)  
- **Model**: `llama3-8b-8192` (Groq)  
- **Chunking**: Size = `500`, Overlap = `100`  

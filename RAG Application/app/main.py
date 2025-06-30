import streamlit as st
from PyPDF2 import PdfReader, errors
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import google.generativeai as genai
import time

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY not set in .env file.")
    st.stop()

genai.configure(api_key=api_key)

# Extract text from PDFs
def fnGetPdfText(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf, strict=False)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        except errors.PdfReadError as e:
            st.error(f"Failed to read a PDF: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
    return text

# Split text into chunks
def fnGetTextChunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    return splitter.split_text(text)

# Create and save FAISS vector store
def fnGetVectorStore(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

# Load QA chain
def fnGetConversationalChain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context.
    If the answer is not in the provided context, just say "Answer is not available in the context."
    Do not make up answers.
    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    prompt = PromptTemplate(template=prompt_template.strip(), input_variables=["context", "question"])
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-8b", temperature=0.3)
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def fnTypewriter(text, delay=0.009):
    placeholder = st.empty()
    displayed_text = "Reply: "
    for char in text:
        displayed_text += char
        placeholder.text(displayed_text)
        time.sleep(delay)
        
# Handle user input
def fnUserInput(user_question):
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)

        chain = fnGetConversationalChain()

        if not docs:
            st.warning("No relevant documents found.")
            return

        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        #response_text = response["output_text"]
        st.write(fnTypewriter(response["output_text"]))
        

    except Exception as e:
        st.error(f"Error running the chain: {e}")
        

# Main Streamlit app
def main():
    st.set_page_config(page_title="Chat PDF", layout="wide")
    st.title("Chat with Your PDFs using Gemini and LangChain")
    st.markdown("Ask any question about your uploaded PDFs using RAG-powered LLM.")

    user_question = st.text_input("Ask a Question")

    if user_question:
        fnUserInput(user_question)

    with st.sidebar:
        st.header("Upload & Process PDFs")
        pdf_docs = st.file_uploader("Upload PDF files", accept_multiple_files=True)
        if st.button("Submit & Process"):
            if not pdf_docs:
                st.warning("Please upload at least one PDF file.")
                return
            with st.spinner("Processing PDFs..."):
                raw_text = fnGetPdfText(pdf_docs)
                if not raw_text.strip():
                    st.error("No extractable text found in the PDFs.")
                    return
                text_chunks = fnGetTextChunks(raw_text)
                fnGetVectorStore(text_chunks)
                st.success(" PDFs processed and indexed!")

if __name__ == "__main__":
    main()

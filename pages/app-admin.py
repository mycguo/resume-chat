#https://www.youtube.com/watch?v=uus5eLz6smA
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import docx  # Import the python-docx library


st.write("API Key", st.secrets["GENAI_API_KEY"])

genai.configure(api_key=st.secrets["GENAI_API_KEY"])


def get_pdf_text(pdf_docs):
    text = ""
    for pdf_doc in pdf_docs:
        pdf = PdfReader(pdf_doc)
        for page in pdf.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=1000)
    chunks = splitter.split_text(text)
    return chunks   

def get_vector_store(text_chunks):
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks,embedding=embedding)
    vector_store.save_local("faiss_index")
    return vector_store


def get_prompt_template():
    return PromptTemplate()

def get_chat_chain():
    prompt_template="""
    Answer the questions based on my resume honestly

    Context:\n {context} \n
    Questions: \n {questions} \n

    Answers:
"""
    model=ChatGoogleGenerativeAI(model="gemini-2.0-flash",temperature=0.3)
    prompt=PromptTemplate(template=prompt_template, input_variabls=["context","questions"],output_variables=["answers"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = vector_store.similarity_search(user_question)

    chain = get_chat_chain()

    response = chain({"input_documents": docs, "questions": user_question}, return_only_outputs=True)              

    print(response)
    st.write("Reply: ",response["output_text"])


def main():
    st.title("Knowledge Assistant")
    st.header("Chat with my local knowledage base")

    user_question = st.text_input("Ask me a question")
    if user_question:
        user_input(user_question)

    with st.sidebar:
        pdf_docs = st.file_uploader("Upload your knowledge base document", type=["pdf"], accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing your PDF documents..."):
                if pdf_docs:
                    text = get_pdf_text(pdf_docs)
                    text_chunks = get_text_chunks(text)
                    vector_store = get_vector_store(text_chunks)
                    get_chat_chain()
                    st.success("Documents processed successfully")

    with st.sidebar:
        st.write("API Key", st.secrets["GENAI_API_KEY"])
        word_docs = st.file_uploader("Upload your knowledge base document", type=["docx"], accept_multiple_files=False)
        if st.button("Submit & Process Word Document"):
            with st.spinner("Processing your word documents..."):
                if word_docs:
                    # Open the file using docx.Document
                    try:
                        doc = docx.Document(word_docs)
                    except Exception as e:
                        st.error(f"Error opening the document: {e}")
                        st.stop()
                    # Example: Extract all paragraphs
                    paragraphs = [p.text for p in doc.paragraphs]
                    st.write("Paragraphs:")
                    for paragraph in paragraphs:
                        st.write(paragraph)
                    text = "\n".join(paragraphs)
                    text_chunks = get_text_chunks(text)
                    vector_store = get_vector_store(text_chunks)
                    get_chat_chain()
                    st.success("Documents processed successfully")

if __name__ == "__main__":
    main()
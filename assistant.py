import os
import ingestion
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
load_dotenv()
from functools import partial

key  =  os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
#  Setup chat model
chat_model = ChatGoogleGenerativeAI(google_api_key=key, model="gemini-1.5-flash")
safety_settings = {
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
# store the original method
og_generate = ChatGoogleGenerativeAI._generate

# patch
ChatGoogleGenerativeAI._generate = partial(chat_model._generate, safety_settings=safety_settings) 

#chat_model = genai.GenerativeModel("gemini-1.5-flash")Answer the question as detailed as possible from the provided context, make sure to provide all the details.
def get_conversational_chain(VectorStore):
    prompt_template = """
    Answer the question as detailed as possible from the provided context which also include the manual name, make sure to provide all the details.
    Provide warnings,cautions and notices if any with the steps in the answer,highlighted in different font type.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Print the "**SOURCES" strictly at the last line of the answer and it should be the product name and Consolidate page numbers of the document from which you got your answer. 
    Be consistent in writing the **SOURCES** format. it should be **SOURCES:** product name , Pages page number or range.
    \n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    #chain = load_qa_chain(chat_model, chain_type="stuff", prompt=prompt)
    #chain = RetrievalQA.from_chain_type(llm=chat_model, chain_type="stuff", retriever=VectorStore, return_source_documents=True,chain_type_kwargs={"prompt": prompt})
    chain = ConversationalRetrievalChain.from_llm(chat_model,VectorStore,return_source_documents=True,combine_docs_chain_kwargs={"prompt": prompt})
    return chain


def get_chain(product_name,manual_name):
    print("product_name",product_name)
    print("manual_name",manual_name)
    filters = {
        "product": product_name,
        "manual_type": manual_name
    }
    #ingestion.save_pdf_embed(["DMR244663_zen0.pdf","D001026163_Rev_E_Planned_Maintenance_Level_1_Zenition_50_70.pdf"])
    db = ingestion.get_retriever()
    retriever = db.as_retriever(search_type ="similarity",search_kwargs={"k":3,"filter":filters})
    """
    # Retrieve documents to check if filters are applied correctly
    relevant_docs = retriever.invoke("How to replace the collimator")

    # Debug: Print the retrieved documents and their metadata
    for doc in relevant_docs:
        #st.write(f"Retrieved document metadata: {doc.metadata}")
        print("METADATA0000000000000",doc.metadata)
    """
    chain = get_conversational_chain(retriever)
    return chain,db

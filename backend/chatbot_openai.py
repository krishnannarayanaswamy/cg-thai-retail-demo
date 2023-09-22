import os
import streamlit as st
import dotenv

#from thai_eval import db
from langchain.llms import OpenAI
from langchain.llms import Cohere
from langchain.vectorstores import Cassandra
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import json
from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
import langchain
from langchain.schema import BaseRetriever
from langchain.schema import Document
from pydantic import BaseModel

langchain.debug = True

dotenv.load_dotenv(dotenv.find_dotenv())

st.set_page_config(layout="wide")


class AstraProductRetriever(BaseRetriever):
    session: Session
    embedding: OpenAIEmbeddings
 
    class Config:
        arbitrary_types_allowed = True
 
    def get_relevant_documents(self, query):
        docs = []
        embeddingvector = self.embedding.embed_query(query)
        column = "openai_description_embedding_en"
        query = SimpleStatement(
        f"""
        SELECT product_id, brand,saleprice,product_categories, product_name_en, short_description_en, long_description_en
        FROM hybridretail.products_cg_hybrid
        ORDER BY {column} ANN OF {embeddingvector}
        LIMIT 5 """
        )

        results = session.execute(query)
        top_products = results._current_rows

        for r in top_products:
            docs.append(Document(
                page_content=r.product_name_en,
                metadata={"product id": r.product_id,"brand" : r.brand, "product category" : r.product_categories, "product name": r.product_name_en, "description" : r.short_description_en}
            ))
 
        return docs


def get_astra_session(scb: str, secrets: str) -> Session:
    """
    Connect to Astra DB using secure connect bundle and credentials.

    Parameters
    ----------
    scb : str
        Path to secure connect bundle.
    secrets : str
        Path to credentials.
    """

    cloud_config = {
        'secure_connect_bundle': scb
    }

    with open(secrets) as f:
        secrets = json.load(f)

    CLIENT_ID = secrets["clientId"]
    CLIENT_SECRET = secrets["secret"]

    auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    return cluster.connect()


@st.cache_resource
def get_session():
    print('Connecting to Astra DB...')
    return get_astra_session(scb='./config/secure-connect-multilingual.zip',
                       secrets='./config/multilingual-token.json')


session = get_session()

#cohere_embedding = O(model='embed-multilingual-v2.0',)
embedding = OpenAIEmbeddings()
retriever = AstraProductRetriever(session=session, embedding=embedding)

#product_store = Cassandra(embedding=cohere_embedding,
#                          session=session,
#                          keyspace='bench',
#                          table_name='bench_cohere_en')
#chat_history_store = Cassandra(embedding=cohere_embedding,
#                               session=session,
#                               keyspace='bench',
#                               table_name='chat_history')

#cohere = Cohere(cohere_api_key=os.environ['COHERE_API_KEY'])

template = """Given the following chat history and a follow up question, rephrase the follow up input question to be a standalone question.
Or end the conversation if it seems like it's done.
Chat History:\"""
{chat_history}
\"""
Follow Up Input: \"""
{question}
\"""
Standalone question:"""

product_list_prompt = PromptTemplate.from_template(template)
 
template = """You are a friendly, conversational home improvement retail shopping assistant. Use the following context including product names, descriptions, and keywords to show the shopper whats available, help find what they want, and answer any questions.
 
It's ok if you don't know the answer.
Context:\"""
 
{context}
\"""
Question:\"
\"""
 
Helpful Answer:"""
 
qa_prompt= PromptTemplate.from_template(template)

#template = """You are a customer service of a home improvement store and you are asked to pick products for a customer.
#Question: {question}
#"""
## Answer: Return the list of items only containing descriptions in JSON String Array format.

#product_list_prompt = PromptTemplate.from_template(template)

#template = """You are a friendly, conversational home improvement store shopping assistant. Use the following context including product names and descriptions to show the shopper whats available, help find what they want, and answer any questions.
 
#It's ok if you don't know the answer.
#Context:\"""
 
#{context}
#\"""
#History:\"""

#{chat_history}

#\"""
#Question:\"
#\"""
 
#Helpful Answer:
#"""
llm = OpenAI(temperature=0)
#qa_prompt = PromptTemplate.from_template(template)

question_generator = LLMChain(
    llm=llm,
    prompt=product_list_prompt
)

doc_chain = load_qa_chain(
    llm=llm,
    chain_type="stuff",
    prompt=qa_prompt
)

#query = 

# chain = LLMChain(prompt=prompt, llm=cohere)
# chain = ConversationalRetrievalChain.from_llm(
#     cohere, retriever=product_store.as_retriever())
chatbot = ConversationalRetrievalChain(
    retriever=retriever,
    combine_docs_chain=doc_chain,
    question_generator=question_generator
)

if 'history' not in st.session_state:
    st.session_state['history'] = []


def conversational_chat(query):
    result = result = chatbot(
        {"question": query, "chat_history": st.session_state['history']}
    )
    st.session_state['history'].append((result["question"], result["answer"]))

    return result["answer"]


for (query, answer) in st.session_state['history']:
    with st.chat_message("User"):
        st.write(query)
    with st.chat_message("Bot"):
        st.write(answer)

# I'd like to build a small fish tank. Could you suggest the products I need to purchase?
prompt = st.chat_input(placeholder="What do you want to build?")
if prompt:
    answer = conversational_chat(prompt)
    (answer)

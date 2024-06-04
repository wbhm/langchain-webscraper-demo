import gradio
import logging
import pandas as pd
import os
import tiktoken
from langchain.text_splitter import TokenTextSplitter
from langchain.vectorstores.pgvector import PGVector, DistanceStrategy
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import DataFrameLoader
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Build the PGVector Connection String from params
host = os.environ['DB_HOST']
port = os.environ['DB_PORT']
user = os.environ['DB_USER']
password = os.environ['DB_PWD']
dbname = os.environ['DB_NAME']

# use postgresql rather than postgres in the conn string since LangChain uses sqlalchemy under the hood
CONNECTION_STRING = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

data_frame = pd.read_csv('samples/blog_post_data.csv')
data_frame.head()

text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=103)


# Helper func: calculate number of tokens
def num_tokens_from_string(string: str, encoding_name="cl100k_base") -> int:
    if not string:
        return 0
    # Returns the number of tokens in a text string
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


# list for smaller chunked text and metadata
new_list = []

# Create a new list by splitting up text into token sizes of around 512 tokens
for i in range(len(data_frame.index)):
    text = data_frame['content'][i]
    token_len = num_tokens_from_string(text)
    if token_len <= 512:
        new_list.append([data_frame['title'][i],
                         data_frame['content'][i],
                         data_frame['url'][i]])
    else:
        # split text into chunks using text splitter
        split_text = text_splitter.split_text(text)
        for j in range(len(split_text)):
            new_list.append([data_frame['title'][i],
                             split_text[j],
                             data_frame['url'][i]])


new_data_frame = pd.DataFrame(new_list, columns=['title', 'content', 'url'])
new_data_frame.head()

#load documents from Pandas dataframe for insertion into database


# page_content_column is the column name in the dataframe to create embeddings for
loader = DataFrameLoader(new_data_frame, page_content_column = 'content')
docs = loader.load()


embeddings = OpenAIEmbeddings()

# Create OpenAI embedding using LangChain's OpenAIEmbeddings class
query_string = "PostgreSQL is my favorite database"
embed = embeddings.embed_query(query_string)
print(len(embed)) # Should be 1536, the dimensionality of OpenAI embeddings
print(embed[:5]) # Should be a list of floats

# Create a PGVector instance to house the documents and embeddings
db = PGVector.from_documents(
    documents= docs,
    embedding = embeddings,
    collection_name= "blog_posts",
    distance_strategy = DistanceStrategy.COSINE,
    connection_string=CONNECTION_STRING)

# Query for which we want to find semantically similar documents
query = "Tell me about how Edeva uses Timescale?"

# Fetch the k=3 most similar documents
docs =  db.similarity_search(query, k=3)

# Interact with a document returned from the similarity search on pgvector
doc = docs[0]

# Access the document's content
doc_content = doc.page_content
# Access the document's metadata object
doc_metadata = doc.metadata

print("Content snippet:" + doc_content[:500])
print("Document title: " + doc_metadata['title'])
print("Document url: " + doc_metadata['url'])

# Create retriever from database
# We specify the number of results we want to retrieve (k=3)
retriever = db.as_retriever(
    search_kwargs={"k": 3}
    )

llm = ChatOpenAI(temperature = 0.0, model = 'gpt-3.5-turbo-16k')

qa_stuff = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    verbose=True,
)

query =  "How does Edeva use continuous aggregates?"

response = qa_stuff.run(query)

 # add gradio code here to display chatbot interface

print(response)

# New chain to return context and sources
qa_stuff_with_sources = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    verbose=True,
)

query =  "How does Edeva use continuous aggregates?"

# To run the query, we use a different syntax since we're returning more than just the response text
responses = qa_stuff_with_sources({"query": query})

source_documents = responses["source_documents"]
source_content = [doc.page_content for doc in source_documents]
source_metadata = [doc.metadata for doc in source_documents]


# Construct a single string with the LLM output and the source titles and urls
def construct_result_with_sources():
    result = responses['result']
    result += "\n\n"
    result += "Sources used:"
    for i in range(len(source_content)):
        result += "\n\n"
        result += source_metadata[i]['title']
        result += "\n\n"
        result += source_metadata[i]['url']

    return result

print(construct_result_with_sources())



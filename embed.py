import os
import re
import logging
import concurrent.futures

from langchain.document_loaders import (
    BSHTMLLoader,
    DirectoryLoader,
)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

from dotenv import load_dotenv

def process_document(document, regex):
    source = regex.sub('', document.metadata['source']).replace('ssl_','https://').replace('.html','').replace('_', '.').replace('=', '/').rstrip('-')
    document.metadata["source"] = source
    return document

def main():
    load_dotenv()
    scrape_dir = os.getenv("SCRAPE_DIR", './scrape')
    chroma_dir = os.getenv("CHROMA_DIR", './chroma')
    if os.path.exists(chroma_dir):
        print("already embedded")
        exit(0)
    try:
        loader = DirectoryLoader(
            scrape_dir,
            glob="*.html",
            loader_cls=BSHTMLLoader,
            show_progress=True,
            loader_kwargs={"get_text_separator": " "},
        )
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        data = loader.load()
        documents = text_splitter.split_documents(data)

        regex = re.compile(r'scrape\\')

        with concurrent.futures.ProcessPoolExecutor() as executor:
            documents = list(executor.map(process_document, documents, [regex]*len(documents)))

        embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
        db = Chroma.from_documents(documents, embedding_model, persist_directory=chroma_dir)
        db.persist()
    except Exception as e:
        logging.error(f"An error has occurred: {e}")


if __name__ == "__main__":
    main()
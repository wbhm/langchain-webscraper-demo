import gradio
import json

from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_qa_with_sources_chain, LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain

load_dotenv()

db = None
llm = None
memory = None
condense_question_chain = None
qa_chain = None
doc_prompt = None
final_qa_chain = None
retrieval_qa = None


def initialize():
    global db, llm, memory, condense_question_chain, qa_chain, doc_prompt, final_qa_chain, retrieval_qa

    db = Chroma(
        persist_directory="./chroma",
        embedding_function=OpenAIEmbeddings(model="text-embedding-ada-002"),
    )

    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    condense_question_prompt = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.\
    Make sure to avoid using any unclear pronouns.

    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:"""
    condense_question_prompt = PromptTemplate.from_template(condense_question_prompt)
    condense_question_chain = LLMChain(
        llm=llm,
        prompt=condense_question_prompt,
    )

    qa_chain = create_qa_with_sources_chain(llm)

    doc_prompt = PromptTemplate(
        template="Content: {page_content}\nSource: {source}",
        input_variables=["page_content", "source"],
    )

    final_qa_chain = StuffDocumentsChain(
        llm_chain=qa_chain,
        document_variable_name="context",
        document_prompt=doc_prompt,
    )

    retrieval_qa = ConversationalRetrievalChain(
        question_generator=condense_question_chain,
        retriever=db.as_retriever(),
        memory=memory,
        combine_docs_chain=final_qa_chain,
    )


def predict(message, history):
    if db is None:
        initialize()

    print(message)
    print(history)

    response = retrieval_qa.run({"question": message})
    print(response)

    response_dict = json.loads(response)
    answer = response_dict["answer"]
    sources = response_dict["sources"]

    if isinstance(sources, list):
        sources = "\n".join(sources)

    if sources:
        return "\n\n".join([answer, "See more:", sources])
    return answer


gradio.ChatInterface(predict).launch()

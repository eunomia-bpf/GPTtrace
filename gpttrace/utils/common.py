import os
import pygments
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import PygmentsTokens
from pygments_markdown_lexer import MarkdownLexer
from typing import Any
from langchain import ConversationChain, OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from llama_index import LLMPredictor, ServiceContext, StorageContext, VectorStoreIndex, SimpleDirectoryReader, load_index_from_storage

from gpttrace.config import cfg

def get_doc_content_for_query(index: VectorStoreIndex, query: str) -> str:
    """
    Find the content from the document that is closest to the user's request

    :param index: Vector database
    :param query: User's request
    :return: The content that is most relevant to the user's request.
    """
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    related_contents = response.source_nodes
    if related_contents is not None:
        contents = "\nThere are some related information about this query:\n"
        for i, content in enumerate(related_contents):
            info = f"Info {i}: {content.node.get_text()}\n"
            contents += info
        return contents
    else:
        return None

def pretty_print(input_info: str, lexer: Any = MarkdownLexer, *args: Any, **kwargs: Any) -> None:
    """
    This function takes an input string and a lexer (default is MarkdownLexer), 
    lexes the input using the provided lexer, and then pretty prints the lexed tokens.
    
    :param input: The string to be lexed and pretty printed.
    :param lexer: The lexer to use for lexing the input. Defaults to MarkdownLexer.
    :param args: Additional arguments to be passed to the print_formatted_text function.
    :param kwargs: Additional keyword arguments to be passed to the print_formatted_text function.
    """
    tokens = list(pygments.lex(input_info, lexer=lexer()))
    print_formatted_text(PygmentsTokens(tokens), *args, **kwargs)

def init_conversation(need_train: bool, verbose: bool) -> list[ConversationChain, VectorStoreIndex]:
    """
    Initialize the conversation and vector database.

    :param need_train: Whether you need to use a vector database.
    :verbose: Whether to print extra information.
    :return: Containing two elements: The ConversationChain object is a conversation between a human and an AI. The VectorStoreIndex object is vector database.
    """
    model_name = cfg.get("DEFAULT_MODEL")
    llm = ChatOpenAI(model_name=model_name, temperature=0)
    agent_chain = ConversationChain(llm=llm, verbose=verbose,
                                    memory=ConversationBufferMemory())
    if need_train:
        vector_path = cfg.get("VECTOR_DATABASE_PATH")
        if not os.path.exists(vector_path):
            print(f"{vector_path} not found. Training...")
            md_files = []
            # Get all markdown files in the tutorial
            for root, _, files in os.walk(cfg.get("DOC_PATH")):
                for file in files:
                    if file.endswith('.md'):
                        md_files.append(os.path.join(root, file))
            print(f":: {cfg.get('DOC_PATH')}, {md_files}")
            documents = SimpleDirectoryReader(input_files=md_files).load_data()
            llm_predictor = LLMPredictor(llm=OpenAI(
                temperature=0, model_name="text-davinci-003"))
            service_context = ServiceContext.from_defaults(
                llm_predictor=llm_predictor)
            index = VectorStoreIndex.from_documents(
                documents, service_context=service_context)
            index.storage_context.persist(vector_path)
            print(
                f"Training completed, {vector_path} has been saved.")
        else:
            print(f"Loading the {vector_path}...")
            storage_context = StorageContext.from_defaults(
                persist_dir=vector_path)
            index = load_index_from_storage(storage_context)
    else:
        index = None
    return agent_chain, index

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.storage import LocalFileStore
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import create_kv_docstore
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Retriever:
    def __init__(self, settings):
        self.settings = settings

    def base(self):
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = Chroma(
            persist_directory=self.settings.CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
            collection_name=self.settings.CHROMA_COLLECTION_NAME
        )
        retriever = vectorstore.as_retriever(
            search_type="similarity",  # 相似度搜索
            search_kwargs={"k": 3})  # 返回前3个结果
        return retriever


    def parent_doc(self):
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        vectorstore = Chroma(
            collection_name=self.settings.CHROMA_COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=self.settings.CHROMA_PERSIST_DIR,

        )
        fs = LocalFileStore(self.settings.LOCALFILESTORE_DIR)
        docstore = create_kv_docstore(fs)
        dummy_splitter = RecursiveCharacterTextSplitter()

        retriever = ParentDocumentRetriever(
            vectorstore=vectorstore,
            docstore=docstore,
            child_splitter=dummy_splitter,  # 塞個空殼給它
            parent_splitter=dummy_splitter  # 塞個空殼給它
        )
        return retriever

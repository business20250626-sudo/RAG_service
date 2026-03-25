from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.storage import LocalFileStore
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import create_kv_docstore
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Retriever:
    def __init__(self, settings):
        self.settings = settings
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self._vectorstore = None
        self._docstore = None

    @property
    def vectorstore(self):
        """單例模式獲取 VectorStore"""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                persist_directory=self.settings.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings,
                collection_name=self.settings.CHROMA_COLLECTION_NAME
            )
        return self._vectorstore

    @property
    def docstore(self):
        """單例模式獲取 DocStore (給 ParentDocument 使用)"""
        if self._docstore is None:
            fs = LocalFileStore(self.settings.LOCALFILESTORE_DIR)
            self._docstore = create_kv_docstore(fs)
        return self._docstore

    def get_base_retriever(self, query: str, k: int = 3, filters: dict = None):
        """基礎檢索器"""
        search_kwargs = {"k": k}
        if filters:
            search_kwargs["filter"] = filters
        retriever = self.vectorstore.as_retriever(
            query=query,
            search_type="similarity",
            search_kwargs=search_kwargs
        )
        return retriever

    def get_parent_retriever(self, query, k: int = 3, filters: dict = None):
        """Parent-Child 檢索器"""
        dummy_splitter = RecursiveCharacterTextSplitter()

        retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            child_splitter=dummy_splitter,
            parent_splitter=dummy_splitter,
            search_kwargs={"k": k, "filter": filters} if filters else {"k": k}
        )
        return retriever






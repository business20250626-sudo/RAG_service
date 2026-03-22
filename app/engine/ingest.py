import os
import shutil
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import Settings
from langchain.storage import LocalFileStore
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import create_kv_docstore
import yaml
import json
import hashlib
import re
from pathlib import Path
from langchain.schema import Document


def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        file_content = f.read()
    # 確保 config 順序一致以維持 hash 穩定
    config_str = json.dumps(Settings.BASE_RAG_CONFIG, sort_keys=True).encode('utf-8')
    return hashlib.md5(file_content + config_str).hexdigest()


def _load_manifest():
    """讀取本地清單，如果不存在則回傳空字典"""
    if os.path.exists(Settings.MANIFEST_DIR):
        with open(Settings.MANIFEST_DIR, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}



# 在 ingest.py 的邏輯中
def incremental_ingest():
    to_add_paths = []
    new_manifest = {}
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(
        collection_name=Settings.CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=Settings.CHROMA_PERSIST_DIR,

    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=50,  # 小块：精确检索
        chunk_overlap=20
    )
    fs = LocalFileStore(Settings.LOCALFILESTORE_DIR)
    docstore = create_kv_docstore(fs)
    # 父文档分割器（用于返回）
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,  # 大块：保持上下文
        chunk_overlap=50
    )
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=docstore,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,

    )
    all_existing_data = vectorstore.get(include=['metadatas'])
    existing_hashes = {meta['file_hash'] for meta in all_existing_data['metadatas'] if 'file_hash' in meta}
    current_file_paths = list(Path(Settings.DATA_DIR).glob("**/*.txt"))
    for file_path in current_file_paths:
        file_name = file_path.name
        current_hash = get_file_hash(file_path)
        new_manifest[file_name] = current_hash

        if current_hash not in existing_hashes:
            to_add_paths.append(file_path)

    all_current_hashes = set(new_manifest.values())
    to_delete_hashes = list(existing_hashes - all_current_hashes)
    if to_delete_hashes:
        vectorstore.delete(where={"file_hash": {"$in": to_delete_hashes}})
        print(f"🗑️ 已從向量庫移除 {len(to_delete_hashes)} 筆過時數據")

    if to_add_paths:
        for file_path in to_add_paths:
            loader =TextLoader(str(file_path), encoding='utf-8')
            single_file_docs = loader.load()
            current_hash = get_file_hash(file_path)
            metadata_pattern = r'^---\s*(.*?)\s*---\s*'
            pattern = r'\n##\s*'
            sections = re.split(pattern, '\n' + single_file_docs[0].page_content.strip())

            # 過濾掉開頭可能產生的空字串
            sections = [s for s in sections if s.strip()]
            parent_docs = []
            chunk_metadata = yaml.safe_load(re.search(metadata_pattern, sections[0].strip().replace('\r\n', '\n'), re.DOTALL).group(1))
            for key, value in chunk_metadata.items():
                if isinstance(value, list):
                    chunk_metadata[key] = ", ".join(map(str, value))
            chunk_metadata['file_hash'] = current_hash
            chunk_metadata['source'] = str(file_path)
            for section in sections[1:]:
                match = re.search(r"關聯職業[：:]\s*(.*)", section)
                if match:
                    career = match.group(1).strip()
                    chunk_metadata["relation_career"] = career
                match = re.search(r"entity_name[：:]\s*(.*)", section)
                if match:
                    chunk_metadata["entity_name"] = match.group(1).strip()
                parent_doc = Document(
                    page_content=section,
                    metadata=chunk_metadata
                )
                parent_docs.append(parent_doc)
            retriever.add_documents(parent_docs, ids=None)
        with open(Settings.MANIFEST_DIR, 'w', encoding='utf-8') as f:
            json.dump(new_manifest, f, ensure_ascii=False, indent=4)


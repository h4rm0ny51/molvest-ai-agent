import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, BSHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class KnowledgeBaseManager:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)

    def load_document(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден.")

        ext = file_path.lower().split('.')[-1]
        if ext == 'pdf':
            loader = PyPDFLoader(file_path)
        elif ext == 'docx':
            loader = Docx2txtLoader(file_path)
        elif ext == 'md':
            loader = TextLoader(file_path, encoding='utf-8')
        elif ext == 'html':
            loader = BSHTMLLoader(file_path, open_encoding='utf-8')
        else:
            raise ValueError("Поддерживаются только форматы: .pdf, .docx, .md, .html")

        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)
        self.vector_store.add_documents(chunks)
        print(f"[{file_path}] Успешно загружено фрагментов: {len(chunks)}")

    def clear_database(self):
        """Удаляет всю информацию из базы знаний для предотвращения дубликатов."""
        try:
            self.vector_store.delete_collection()
            self.vector_store = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
            print("База данных успешно очищена.")
        except Exception as e:
            print(f"Ошибка при очистке базы данных: {e}")

    def search_similar(self, query: str, top_k: int = 3):
        return self.vector_store.similarity_search(query, k=top_k)
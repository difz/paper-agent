"""
User-specific vector store manager for Discord bot.
Each user gets their own isolated ChromaDB collection.
"""
import os
import glob
import logging
from typing import Optional, List
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from .config import Settings
from .pdf_metadata import extract_pdf_metadata

log = logging.getLogger("user_store_manager")


class UserStoreManager:
    """Manages per-user vector stores for PDF indexing."""

    def __init__(self, base_dir: str = "./store/users"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.settings = Settings()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " "]
        )

    def _get_user_dir(self, user_id: str) -> Path:
        """Get the directory for a specific user's vector store."""
        user_dir = self.base_dir / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _get_pdf_dir(self, user_id: str) -> Path:
        """Get the directory for a user's uploaded PDFs."""
        pdf_dir = self._get_user_dir(user_id) / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        return pdf_dir

    def _get_chroma_dir(self, user_id: str) -> Path:
        """Get the ChromaDB directory for a user."""
        chroma_dir = self._get_user_dir(user_id) / "chroma"
        chroma_dir.mkdir(parents=True, exist_ok=True)
        return chroma_dir

    def save_pdf(self, user_id: str, pdf_content: bytes, filename: str) -> str:
        """
        Save a PDF file for a user.

        Args:
            user_id: Discord user ID
            pdf_content: PDF file content in bytes
            filename: Original filename

        Returns:
            Path to saved PDF
        """
        pdf_dir = self._get_pdf_dir(user_id)
        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        pdf_path = pdf_dir / safe_filename

        with open(pdf_path, "wb") as f:
            f.write(pdf_content)

        log.info(f"Saved PDF for user {user_id}: {safe_filename}")
        return str(pdf_path)

    def get_user_pdfs(self, user_id: str) -> List[str]:
        """Get list of PDF files for a user."""
        pdf_dir = self._get_pdf_dir(user_id)
        return glob.glob(str(pdf_dir / "*.pdf"))

    def build_user_index(self, user_id: str) -> int:
        """
        Build or update the vector store index for a user's PDFs.

        Args:
            user_id: Discord user ID

        Returns:
            Number of chunks indexed
        """
        pdfs = self.get_user_pdfs(user_id)
        if not pdfs:
            log.warning(f"No PDFs found for user {user_id}")
            return 0

        # Load all PDFs with metadata extraction
        docs = []
        for pdf_path in pdfs:
            try:
                log.info(f"Processing {os.path.basename(pdf_path)}...")

                # Extract bibliographic metadata
                pdf_metadata = extract_pdf_metadata(pdf_path)
                log.info(f"  Title: {pdf_metadata.get('title', 'Unknown')}")
                log.info(f"  Authors: {', '.join(pdf_metadata.get('authors', [])) or 'Unknown'}")
                log.info(f"  Year: {pdf_metadata.get('year', 'Unknown')}")

                # Load PDF pages
                loader = PyPDFLoader(pdf_path)
                for d in loader.load():
                    # Add bibliographic metadata to each page's metadata
                    d.metadata['bib_title'] = pdf_metadata.get('title')
                    d.metadata['bib_authors'] = pdf_metadata.get('authors', [])
                    d.metadata['bib_year'] = pdf_metadata.get('year')
                    d.metadata['bib_journal'] = pdf_metadata.get('journal')
                    d.metadata['bib_doi'] = pdf_metadata.get('doi')
                    docs.append(d)

                log.info(f"Loaded PDF: {os.path.basename(pdf_path)}")
            except Exception as e:
                log.error(f"Error loading {pdf_path}: {e}")

        if not docs:
            return 0

        # Split into chunks
        chunks = self.splitter.split_documents(docs)

        # Create or update ChromaDB
        chroma_dir = self._get_chroma_dir(user_id)
        emb = GoogleGenerativeAIEmbeddings(model=self.settings.embed_model)

        # Check if collection exists, if so, delete and recreate
        # This ensures we don't have duplicate chunks
        if (chroma_dir / "chroma.sqlite3").exists():
            log.info(f"Updating existing index for user {user_id}")

        vs = Chroma.from_documents(
            chunks,
            embedding=emb,
            persist_directory=str(chroma_dir)
        )
        vs.persist()

        log.info(f"Built index for user {user_id}: {len(chunks)} chunks from {len(pdfs)} PDFs")
        return len(chunks)

    def get_retriever(self, user_id: str, top_k: Optional[int] = None):
        """
        Get a retriever for a user's vector store.

        Args:
            user_id: Discord user ID
            top_k: Number of results to retrieve (default from settings)

        Returns:
            LangChain retriever or None if no index exists
        """
        chroma_dir = self._get_chroma_dir(user_id)

        # Check if index exists
        if not (chroma_dir / "chroma.sqlite3").exists():
            log.warning(f"No index found for user {user_id}")
            return None

        k = top_k or self.settings.top_k
        emb = GoogleGenerativeAIEmbeddings(model=self.settings.embed_model)
        vs = Chroma(persist_directory=str(chroma_dir), embedding_function=emb)

        return vs.as_retriever(search_kwargs={"k": k})

    def clear_user_data(self, user_id: str) -> bool:
        """
        Clear all data for a user (PDFs and vector store).

        Args:
            user_id: Discord user ID

        Returns:
            True if successful
        """
        import shutil

        user_dir = self._get_user_dir(user_id)
        if user_dir.exists():
            shutil.rmtree(user_dir)
            log.info(f"Cleared all data for user {user_id}")
            return True
        return False

    def get_user_stats(self, user_id: str) -> dict:
        """
        Get statistics about a user's data.

        Returns:
            Dict with pdf_count, total_size, has_index
        """
        pdfs = self.get_user_pdfs(user_id)
        total_size = sum(os.path.getsize(pdf) for pdf in pdfs)
        chroma_dir = self._get_chroma_dir(user_id)
        has_index = (chroma_dir / "chroma.sqlite3").exists()

        return {
            "pdf_count": len(pdfs),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "has_index": has_index,
            "pdf_names": [os.path.basename(p) for p in pdfs]
        }

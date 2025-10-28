import os, glob, logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from .config import Settings
from .logging_conf import setup_logging
from .pdf_metadata import extract_pdf_metadata

log = logging.getLogger("build_index")

def build_index(corpus_dir: str = "./corpus"):
    setup_logging()
    s = Settings()
    pdfs = glob.glob(os.path.join(corpus_dir, "*.pdf"))
    if not pdfs:
        log.warning("No PDFs found in %s", corpus_dir); return

    docs = []
    for p in pdfs:
        log.info(f"Processing {os.path.basename(p)}...")

        # Extract bibliographic metadata
        pdf_metadata = extract_pdf_metadata(p)
        log.info(f"  Title: {pdf_metadata.get('title', 'Unknown')}")
        log.info(f"  Authors: {', '.join(pdf_metadata.get('authors', [])) or 'Unknown'}")
        log.info(f"  Year: {pdf_metadata.get('year', 'Unknown')}")

        # Load PDF pages
        for d in PyPDFLoader(p).load():     # one Document per page
            # Add bibliographic metadata to each page's metadata
            # Convert authors list to string (ChromaDB doesn't support list metadata)
            authors_list = pdf_metadata.get('authors', [])
            authors_str = "; ".join(authors_list) if authors_list else None

            d.metadata['bib_title'] = pdf_metadata.get('title')
            d.metadata['bib_authors'] = authors_str  # Store as string
            d.metadata['bib_year'] = pdf_metadata.get('year')
            d.metadata['bib_journal'] = pdf_metadata.get('journal')
            d.metadata['bib_doi'] = pdf_metadata.get('doi')
            docs.append(d)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(docs)

    emb = GoogleGenerativeAIEmbeddings(model=s.embed_model)  # text-embedding-004
    vs = Chroma.from_documents(chunks, embedding=emb, persist_directory=s.chroma_dir)
    vs.persist()
    log.info("Built Chroma index at %s with %d chunks", s.chroma_dir, len(chunks))
    return s.chroma_dir

if __name__ == "__main__":
    build_index()

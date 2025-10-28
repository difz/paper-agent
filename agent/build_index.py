import os, glob, logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from .config import Settings
from .logging_conf import setup_logging

log = logging.getLogger("build_index")

def build_index(corpus_dir: str = "./corpus"):
    setup_logging()
    s = Settings()
    pdfs = glob.glob(os.path.join(corpus_dir, "*.pdf"))
    if not pdfs:
        log.warning("No PDFs found in %s", corpus_dir); return

    docs = []
    for p in pdfs:
        for d in PyPDFLoader(p).load():     # one Document per page
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

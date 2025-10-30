import os, glob, logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from .config import Settings
from .logging_conf import setup_logging
from .pdf_metadata import extract_pdf_metadata

log = logging.getLogger("build_index")

def build_index(corpus_dir: str = "./corpus"):
    """
    Membangun dan menyimpan indeks vektor (Chroma) dari kumpulan dokumen PDF ilmiah.

    Deskripsi
    ----------
    Fungsi ini melakukan proses ekstraksi, pembagian, dan embedding teks dari sekumpulan PDF
    di direktori tertentu untuk membentuk **Chroma vector store**, yang kemudian dapat digunakan
    untuk pencarian semantik atau retrieval berbasis konteks (RAG - Retrieval-Augmented Generation).

    Fungsi ini berperan sebagai tahap *preprocessing dan indexing pipeline* untuk sistem
    asisten riset berbasis LLM. Setiap halaman dari dokumen PDF akan diperlakukan sebagai satu
    unit dokumen kecil (page-level document), dengan metadata bibliografis yang disertakan agar
    hasil pencarian lebih informatif.

    Parameter
    ----------
    corpus_dir : str, opsional (default: "./corpus")
        Jalur direktori tempat file PDF sumber disimpan. Semua file dengan ekstensi `.pdf`
        di direktori ini akan diproses dan dimasukkan ke dalam indeks.

    Alur Kerja
    ----------
    1. **Inisialisasi dan pemeriksaan sumber data**
       - Memanggil `setup_logging()` untuk menyiapkan logging runtime.
       - Mengambil konfigurasi dari kelas `Settings()` (misalnya model embedding dan direktori penyimpanan).
       - Memindai semua file PDF dalam `corpus_dir` menggunakan `glob.glob()`.

    2. **Ekstraksi metadata dan konten PDF**
       - Untuk setiap PDF, diekstrak metadata bibliografi (judul, penulis, tahun, DOI, jurnal).
       - File PDF kemudian dimuat per halaman menggunakan `PyPDFLoader`, menghasilkan satu
         objek `Document` per halaman.
       - Metadata bibliografi disematkan ke setiap halaman untuk keperluan pelacakan sumber
         dan peningkatan hasil pencarian.

    3. **Pemecahan dokumen menjadi potongan teks (chunking)**
       - Menggunakan `RecursiveCharacterTextSplitter` untuk membagi teks per halaman menjadi
         potongan berukuran lebih kecil (~1000 karakter) dengan tumpang tindih (overlap) 150 karakter.
       - Hal ini dilakukan untuk menjaga konteks antar potongan sambil memudahkan embedding.

    4. **Embedding dan penyimpanan vektor**
       - Menggunakan `GoogleGenerativeAIEmbeddings` (model `text-embedding-004`) untuk
         menghasilkan representasi vektor dari setiap potongan teks.
       - Menyimpan hasil embedding ke dalam **Chroma vector store** melalui `Chroma.from_documents()`.
       - Direktori penyimpanan ditentukan oleh `s.chroma_dir` dan akan dipertahankan (persisted)
         secara otomatis oleh LangChain-Chroma.

    5. **Logging dan keluaran**
       - Menampilkan ringkasan jumlah potongan teks yang berhasil diindeks.
       - Mengembalikan path direktori Chroma yang berisi hasil indeks vektor.

    Nilai Kembali
    --------------
    str
        Path direktori tempat indeks Chroma disimpan (`s.chroma_dir`).

    Catatan
    --------
    - Jika tidak ditemukan PDF dalam direktori sumber, fungsi akan menampilkan peringatan
      dan keluar tanpa membuat indeks baru.
    - Metadata disimpan sebagai string (bukan list) karena keterbatasan dukungan tipe data
      pada penyimpanan ChromaDB.
    - Fungsi ini ideal dijalankan sekali sebelum proses RAG atau saat korpus diperbarui.

    Contoh
    --------
    build_index("./data/papers")
    'data/chroma_index'

    """
    setup_logging()
    s = Settings()
    # Ambil semua file PDF dalam direktori korpus
    pdfs = glob.glob(os.path.join(corpus_dir, "*.pdf"))
    if not pdfs:
        log.warning("No PDFs found in %s", corpus_dir); return

    docs = []
    for p in pdfs:
        log.info(f"Processing {os.path.basename(p)}...")

        # Ekstrak metadata bibliografi dari PDF
        pdf_metadata = extract_pdf_metadata(p)
        log.info(f"  Title: {pdf_metadata.get('title', 'Unknown')}")
        log.info(f"  Authors: {', '.join(pdf_metadata.get('authors', [])) or 'Unknown'}")
        log.info(f"  Year: {pdf_metadata.get('year', 'Unknown')}")

        # Muat PDF per halaman menggunakan loader LangChain
        for d in PyPDFLoader(p).load():     # one Document per page
            # Tambahkan metadata bibliografi ke setiap halaman
            authors_list = pdf_metadata.get('authors', [])
            authors_str = "; ".join(authors_list) if authors_list else None

            d.metadata['bib_title'] = pdf_metadata.get('title')
            d.metadata['bib_authors'] = authors_str  # Simpan sebagai string
            d.metadata['bib_year'] = pdf_metadata.get('year')
            d.metadata['bib_journal'] = pdf_metadata.get('journal')
            d.metadata['bib_doi'] = pdf_metadata.get('doi')
            docs.append(d)

    # Pecah teks menjadi potongan yang lebih kecil dengan overlap
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(docs)

    # Buat embedding menggunakan Google Generative AI (Gemini)
    emb = GoogleGenerativeAIEmbeddings(model=s.embed_model)  # text-embedding-004
    # Bangun dan simpan Chroma index secara otomatis
    vs = Chroma.from_documents(chunks, embedding=emb, persist_directory=s.chroma_dir)
    
    log.info("Built Chroma index at %s with %d chunks", s.chroma_dir, len(chunks))
    return s.chroma_dir

if __name__ == "__main__":
    build_index()

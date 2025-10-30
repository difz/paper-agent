from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from .tools_gemini import retrieve_passages, summarize_with_citations
from .search_tools import search_academic_papers
from .config import Settings

def build_agent():
    """
    Membuat dan mengembalikan LangChain Agent
    Description
    -----------
    - Membaca konfigurasi dari `Settings` (mis. nama model LLM, API keys).
    - Menginisialisasi wrapper LLM Google Generative AI (Gemini) dengan parameter deterministik
      untuk keluaran yang konsisten (`temperature=0`).
    - Mendaftarkan tools eksternal yang tersedia untuk agent:
        * `retrieve_passages`         - mengambil kutipan/passage relevan dari dokumen yang diunggah
        * `summarize_with_citations`  - membuat ringkasan yang menyertakan sitasi / sumber
        * `search_academic_papers`    - melakukan pencarian makalah akademik (arXiv/Semantic Scholar/DS)
    - Menggabungkan semuanya ke dalam `create_agent(...)` dan mengembalikan objek agent yang
      siap dipanggil (CompiledStateGraph).

    Behavior expectations (ringkasan singkat)
    ----------------------------------------
    - Untuk pertanyaan umum: jawab langsung mengandalkan pengetahuan bawaan LLM.
    - Untuk pertanyaan yang memerlukan bukti, kutipan, atau pemeriksaan dokumen: gunakan tools.
    - Selalu prioritaskan akurasi; apabila data tidak pasti, berikan pernyataan ketidakpastian dan
      sumber yang digunakan (tool outputs).
    - Jika perlu klarifikasi dari pengguna, minta pertanyaan lanjutan sebelum memanggil tools besar.
    """
    s = Settings()
    llm = ChatGoogleGenerativeAI(model=s.llm_model, temperature=0)
    tools = [
        retrieve_passages,
        summarize_with_citations,
        search_academic_papers
    ]

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are a helpful research assistant. You can:
1. Answer general questions using your knowledge
2. Search and retrieve information from uploaded PDF documents (use retrieve_passages or summarize_with_citations tools)
3. Search for academic papers when needed (use search_academic_papers tool)

Use tools when the user asks about specific documents or needs to find academic papers. For general questions, feel free to answer directly using your knowledge."""
    )

def ask_agent(message: str) -> str:
    """
    Mengirimkan pertanyaan pengguna ke agen LangChain dan mengembalikan respons akhir model dalam bentuk teks.

    Deskripsi
    ----------
    Fungsi ini berperan sebagai antarmuka sederhana antara pengguna dan agen LangChain
    yang telah dikompilasi (dibangun melalui `build_agent`). Fungsi ini menyusun format pesan
    yang sesuai dengan standar LangChain, memanggil agen menggunakan metode `invoke()`, lalu
    mengekstrak respons akhir yang dihasilkan oleh model AI.

    Alur Kerja
    -----------
    1. **Membangun agen (agent graph)**:
       - Memanggil `build_agent()` untuk membuat instance baru dari `CompiledStateGraph`
         yang berisi integrasi antara LLM (Google Generative AI / Gemini) dan tools yang terdaftar.
       - Setiap pemanggilan akan membuat agen baru, sehingga fungsi ini bersifat *stateless*
         (tidak menyimpan riwayat percakapan sebelumnya).

    2. **Menjalankan agen**:
       - Agen dipanggil menggunakan format pesan standar LangChain:
         {
             "messages": [
                 {"role": "user", "content": <pesan_pengguna>}
             ]
         }
       - Metode `invoke()` akan mengeksekusi proses *reasoning* internal, termasuk pemanggilan
         tools eksternal jika diperlukan (misalnya untuk pencarian atau ringkasan dokumen).

    3. **Ekstraksi hasil akhir**:
       - Hasil dari `invoke()` berupa struktur data yang memuat daftar pesan (`messages`).
       - Fungsi ini menelusuri pesan-pesan tersebut dari akhir ke awal untuk mencari pesan dengan tipe `ai`.
       - Konten pesan bisa berupa string tunggal, daftar blok teks, atau objek kompleks lainnya;
         fungsi ini menyesuaikan format keluaran agar dikembalikan sebagai teks yang bersih dan mudah dibaca.

    Nilai Kembali
    --------------
    - Mengembalikan string berisi respons akhir dari agen (jawaban LLM atau hasil tool).
    - Jika tidak ditemukan pesan AI yang valid, fungsi akan mengembalikan representasi teks dari hasil mentah.

    Catatan
    --------
    - Fungsi ini cocok untuk penggunaan langsung (misalnya antarmuka chatbot atau prompt CLI).
    - Untuk aplikasi percakapan berkelanjutan (multi-turn), disarankan menyimpan instance agent
      agar konteks percakapan tetap terjaga.
    """
    agent_graph = build_agent()

    result = agent_graph.invoke(
        {"messages": [{"role": "user", "content": message}]}
    )

    messages = result.get("messages", [])
    if messages:
        for msg in reversed(messages):
            if hasattr(msg, 'content') and hasattr(msg, 'type') and msg.type == 'ai':
                content = msg.content
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and 'text' in block:
                            text_parts.append(block['text'])
                        elif isinstance(block, str):
                            text_parts.append(block)
                    return '\n'.join(text_parts)
                elif isinstance(content, str):
                    return content
                else:
                    return str(content)
                
        if hasattr(messages[-1], 'content'):
            content = messages[-1].content
            if isinstance(content, str):
                return content
            return str(content)
        return str(messages[-1])

    return str(result)

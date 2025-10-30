"""
Manajer Riwayat Percakapan (Conversation Manager)

Modul ini berfungsi untuk mengelola dan menyimpan riwayat percakapan antar pengguna.
Setiap percakapan dicatat secara terstruktur dalam format JSON, lengkap dengan
penanda waktu (timestamp), pertanyaan, jawaban, serta daftar sumber yang digunakan
selama percakapan.

Dengan adanya modul ini, sistem dapat:
1. Mempertahankan konteks percakapan pengguna antar sesi.
2. Menyediakan riwayat yang dapat ditinjau ulang atau ditampilkan kembali.
3. Mengelola pencarian dan penghapusan riwayat dengan mudah.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

log = logging.getLogger("conversation_manager")


class ConversationManager:
    """
    Kelas ini bertugas mengelola riwayat percakapan untuk setiap pengguna.
    Setiap pengguna akan memiliki satu file JSON yang berisi seluruh interaksi
    yang pernah dilakukan dengan sistem.

    Atribut
    -------
    base_dir : str
        Direktori dasar tempat penyimpanan file percakapan pengguna.

    Metode Utama
    -------------
    - add_conversation() : Menyimpan percakapan baru.
    - get_history() : Mengambil riwayat percakapan.
    - get_recent_context() : Mengambil konteks percakapan terakhir.
    - clear_history() : Menghapus seluruh riwayat pengguna.
    - format_history() : Menampilkan riwayat dalam format siap baca.
    - get_all_sources() : Mengambil seluruh sumber unik dari percakapan.
    - search_history() : Mencari topik tertentu dalam riwayat percakapan.
    """

    def __init__(self, base_dir: str = "./store/conversations"):
        """
        Inisialisasi manajer percakapan dengan menentukan direktori penyimpanan.

        Parameter
        ---------
        base_dir : str, opsional
            Jalur direktori tempat riwayat percakapan disimpan.
            Secara default berada di './store/conversations'.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_file(self, user_id: str) -> Path:
        """
        Mendapatkan jalur file percakapan untuk pengguna tertentu.

        Parameter
        ---------
        user_id : str
            ID pengguna.

        Mengembalikan
        -------------
        Path
            Objek Path menuju file JSON pengguna.
        """
        user_file = self.base_dir / f"user_{user_id}.json"
        return user_file

    def add_conversation(self, user_id: str, question: str, answer: str,
                        sources: Optional[List[str]] = None):
        """
        Menambahkan satu entri percakapan baru ke dalam riwayat pengguna.

        Langkah-langkah
        ---------------
        1. Memuat riwayat lama dari file (jika ada).
        2. Membuat entri percakapan baru yang berisi:
            - Waktu percakapan (timestamp ISO 8601)
            - Pertanyaan pengguna
            - Jawaban agen
            - Daftar sumber yang digunakan (jika tersedia)
        3. Menyimpan ulang seluruh riwayat ke dalam file pengguna.

        Parameter
        ---------
        user_id : str
            ID unik pengguna.
        question : str
            Pertanyaan yang diajukan oleh pengguna.
        answer : str
            Jawaban yang diberikan oleh agen.
        sources : list[str], opsional
            Daftar sumber atau referensi yang digunakan.
        """
        user_file = self._get_user_file(user_id)

        # Load existing history
        if user_file.exists():
            with open(user_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = {"user_id": user_id, "conversations": []}

        # Add new conversation
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "sources": sources or []
        }
        history["conversations"].append(conversation)

        # Save
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        log.info(f"Saved conversation for user {user_id}")

    def get_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Mengambil seluruh riwayat percakapan pengguna.

        Parameter
        ---------
        user_id : str
            ID pengguna.
        limit : int, opsional
            Jumlah maksimum percakapan terbaru yang ingin diambil.

        Mengembalikan
        -------------
        list[dict]
            Daftar percakapan yang tersimpan.
        """
        user_file = self._get_user_file(user_id)

        if not user_file.exists():
            return []

        with open(user_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        conversations = history.get("conversations", [])

        if limit:
            conversations = conversations[-limit:]

        return conversations

    def get_recent_context(self, user_id: str, num_turns: int = 3) -> str:
        """
        Mengambil konteks percakapan terbaru dalam format teks yang ringkas.

        Tujuan
        ------
        Fungsi ini berguna untuk menjaga kontinuitas percakapan dengan mengambil
        beberapa percakapan terakhir dan menggabungkannya sebagai konteks bagi agen.

        Parameter
        ---------
        user_id : str
            ID pengguna.
        num_turns : int, opsional
            Jumlah percakapan terakhir yang ingin diambil (default: 3).

        Mengembalikan
        -------------
        str
            Ringkasan konteks percakapan terakhir.
        """
        history = self.get_history(user_id, limit=num_turns)

        if not history:
            return ""

        context_parts = []
        for conv in history:
            context_parts.append(f"Q: {conv['question']}")
            context_parts.append(f"A: {conv['answer'][:200]}...")  # Truncate long answers

        return "\n".join(context_parts)

    def clear_history(self, user_id: str) -> bool:
        """
        Menghapus seluruh riwayat percakapan milik pengguna tertentu.

        Parameter
        ---------
        user_id : str
            ID pengguna.

        Mengembalikan
        -------------
        bool
            True jika penghapusan berhasil, False jika file tidak ditemukan.
        """
        user_file = self._get_user_file(user_id)

        if user_file.exists():
            user_file.unlink()
            log.info(f"Cleared conversation history for user {user_id}")
            return True

        return False

    def format_history(self, user_id: str, limit: int = 10) -> str:
        """
        Menyusun riwayat percakapan agar mudah dibaca atau ditampilkan (misalnya di Discord).

        Parameter
        ---------
        user_id : str
            ID pengguna.
        limit : int, opsional
            Jumlah percakapan terakhir yang ingin ditampilkan (default: 10).

        Mengembalikan
        -------------
        str
            String yang berisi riwayat percakapan dalam format terstruktur.
        """
        history = self.get_history(user_id, limit=limit)

        if not history:
            return "No conversation history found."

        lines = [f"📜 **Your Recent Conversations** (last {len(history)}):\n"]

        for i, conv in enumerate(history, 1):
            timestamp = datetime.fromisoformat(conv['timestamp'])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M")

            lines.append(f"**{i}. {time_str}**")
            lines.append(f"❓ Q: {conv['question']}")

            # Truncate long answers
            answer = conv['answer']
            if len(answer) > 150:
                answer = answer[:150] + "..."

            lines.append(f"💡 A: {answer}")

            if conv.get('sources'):
                lines.append(f"📚 Sources: {len(conv['sources'])}")

            lines.append("")  # Empty line

        return "\n".join(lines)

    def get_all_sources(self, user_id: str) -> List[str]:
        """
        Mengambil semua sumber unik yang pernah dikutip oleh pengguna.

        Parameter
        ---------
        user_id : str
            ID pengguna.

        Mengembalikan
        -------------
        list[str]
            Daftar sumber unik.
        """
        history = self.get_history(user_id)

        all_sources = set()
        for conv in history:
            all_sources.update(conv.get('sources', []))

        return sorted(list(all_sources))

    def search_history(self, user_id: str, query: str) -> List[Dict]:
        """
        Melakukan pencarian berdasarkan kata kunci pada seluruh riwayat percakapan.

        Parameter
        ---------
        user_id : str
            ID pengguna.
        query : str
            Kata kunci pencarian.

        Mengembalikan
        -------------
        list[dict]
            Daftar percakapan yang mengandung kata kunci.
        """
        history = self.get_history(user_id)

        query_lower = query.lower()
        matches = []

        for conv in history:
            if (query_lower in conv['question'].lower() or
                query_lower in conv['answer'].lower()):
                matches.append(conv)

        return matches

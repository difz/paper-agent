"""
Modul utilitas untuk menghasilkan dan mengekspor sitasi dalam berbagai format standar.

Deskripsi
----------
Modul ini menyediakan kelas dan fungsi untuk:
1. Membuat representasi metadata kutipan (`Citation`).
2. Mengonversinya ke berbagai format gaya penulisan seperti:
   - **APA (7th edition)**
   - **MLA (9th edition)**
   - **Chicago Manual of Style**
   - **IEEE**
   - **BibTeX**
3. Mengelola kumpulan sitasi dan membentuk bibliografi terformat
   menggunakan `CitationManager`
"""
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime

log = logging.getLogger("citation_export")


class Citation:
    """
    Kelas `Citation` merepresentasikan satu entitas sitasi ilmiah yang menyimpan 
    seluruh metadata penting dari suatu artikel, jurnal, atau karya akademik.

    Tujuan utama kelas ini adalah menyediakan cara yang mudah untuk:
    - Menyimpan informasi bibliografi dalam satu struktur data yang konsisten.
    - Mengonversi metadata sitasi menjadi berbagai format kutipan standar 
      (BibTeX, APA, MLA, Chicago, IEEE, dan Plain Text).
    
    ---
    ### Atribut
    - **title** (`str`): Judul publikasi.
    - **authors** (`List[str]`): Daftar nama penulis dalam urutan kemunculan.
    - **year** (`str`): Tahun publikasi.
    - **journal** (`str`): Nama jurnal atau konferensi tempat karya diterbitkan.
    - **volume** (`str`): Nomor volume jurnal.
    - **issue** (`str`): Nomor edisi atau issue dari jurnal.
    - **pages** (`str`): Rentang halaman artikel.
    - **doi** (`str`): Digital Object Identifier (DOI) untuk publikasi.
    - **url** (`str`): Tautan langsung ke publikasi.
    - **publisher** (`str`): Nama penerbit (jika relevan).
    - **pdf_file** (`str`): Nama file PDF tempat sumber diambil (jika ada).
    - **page_num** (`str`): Nomor halaman spesifik dalam PDF.

    ---
    ### Contoh Penggunaan
    ```python
    citation = Citation(
        title="Deep Learning for E-Waste Classification",
        authors=["Budi Setiawan", "Galuh A. Insani"],
        year="2025",
        journal="Journal of Sustainable Computing",
        volume="12",
        issue="3",
        pages="45-58",
        doi="10.1234/jsusc.2025.003",
    )

    print(citation.to_apa())
    ```
    """

    def __init__(self, **kwargs):
        """Inisialisasi objek Citation dengan metadata bibliografi."""
        self.title = kwargs.get('title', '')
        self.authors = kwargs.get('authors', [])  # List of author names
        self.year = kwargs.get('year', '')
        self.journal = kwargs.get('journal', '')
        self.volume = kwargs.get('volume', '')
        self.issue = kwargs.get('issue', '')
        self.pages = kwargs.get('pages', '')
        self.doi = kwargs.get('doi', '')
        self.url = kwargs.get('url', '')
        self.publisher = kwargs.get('publisher', '')
        self.pdf_file = kwargs.get('pdf_file', '')
        self.page_num = kwargs.get('page_num', '')

    def to_bibtex(self, cite_key: Optional[str] = None) -> str:
        """
        Menghasilkan format kutipan **BibTeX** untuk publikasi ini.

        Format ini biasanya digunakan dalam sistem LaTeX atau manajer referensi 
        seperti Zotero, Mendeley, dan BibDesk.

        ---
        ### Parameter
        - **cite_key** (`str`, opsional): Kunci sitasi unik yang digunakan dalam file `.bib`.
          Jika tidak diberikan, kunci akan dihasilkan otomatis dari nama belakang 
          penulis pertama dan tahun publikasi (contoh: `Setiawan2025`).

        ---
        ### Return
        - **str**: Representasi kutipan dalam format BibTeX lengkap.

        ---
        ### Contoh
        ```python
        print(citation.to_bibtex())
        ```
        """
        ...
        if not cite_key:
            first_author = self.authors[0].split()[-1] if self.authors else "Unknown"
            cite_key = f"{first_author}{self.year}"

        lines = [f"@article{{{cite_key},"]

        if self.title:
            lines.append(f"  title = {{{self.title}}},")
        if self.authors:
            authors_str = " and ".join(self.authors)
            lines.append(f"  author = {{{authors_str}}},")
        if self.year:
            lines.append(f"  year = {{{self.year}}},")
        if self.journal:
            lines.append(f"  journal = {{{self.journal}}},")
        if self.volume:
            lines.append(f"  volume = {{{self.volume}}},")
        if self.issue:
            lines.append(f"  number = {{{self.issue}}},")
        if self.pages:
            lines.append(f"  pages = {{{self.pages}}},")
        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")
        if self.url:
            lines.append(f"  url = {{{self.url}}},")

        lines.append("}")
        return "\n".join(lines)

    def to_apa(self) -> str:
        """
        Menghasilkan kutipan dalam format **APA Edisi ke-7**.

        Format ini umum digunakan dalam publikasi sosial, psikologi, dan sains terapan.
        Metode ini secara otomatis menangani format nama penulis tunggal, ganda, 
        maupun lebih dari 20 penulis.

        ---
        ### Return
        - **str**: Teks kutipan yang diformat sesuai standar APA.

        ---
        ### Contoh
        ```python
        print(citation.to_apa())
        # Output:
        # Setiawan, B., & Insani, G. A. (2025). Deep Learning for E-Waste Classification. 
        # *Journal of Sustainable Computing*, 12(3), 45-58. https://doi.org/10.1234/jsusc.2025.003
        ```
        """
        ...
        parts = []

        if self.authors:
            if len(self.authors) == 1:
                parts.append(self.authors[0])
            elif len(self.authors) == 2:
                parts.append(f"{self.authors[0]}, & {self.authors[1]}")
            elif len(self.authors) <= 20:
                parts.append(", ".join(self.authors[:-1]) + f", & {self.authors[-1]}")
            else:
                parts.append(", ".join(self.authors[:19]) + ", ... " + self.authors[-1])

        if self.year:
            parts.append(f"({self.year}).")
        else:
            parts.append("(n.d.).")

        if self.title:
            parts.append(f"{self.title}.")

        if self.journal:
            journal_part = f"*{self.journal}*"
            if self.volume:
                journal_part += f", *{self.volume}*"
            if self.issue:
                journal_part += f"({self.issue})"
            if self.pages:
                journal_part += f", {self.pages}"
            parts.append(journal_part + ".")

        if self.doi:
            parts.append(f"https://doi.org/{self.doi}")
        elif self.url:
            parts.append(self.url)

        return " ".join(parts)

    def to_mla(self) -> str:
        """
        Menghasilkan kutipan dalam format **MLA (Modern Language Association)** 
        edisi ke-9.

        Format ini umum dipakai untuk karya dalam bidang humaniora seperti sastra, 
        sejarah, dan filsafat.

        ---
        ### Return
        - **str**: Representasi kutipan dalam format MLA.

        ---
        ### Contoh
        ```python
        print(citation.to_mla())
        # Output:
        # Setiawan, Budi, and Galuh A. Insani. "Deep Learning for E-Waste Classification." 
        # *Journal of Sustainable Computing*, vol. 12, no. 3, 2025, pp. 45-58. https://doi.org/10.1234/jsusc.2025.003.
        ```
        """
        ...
        parts = []

        if self.authors:
            if len(self.authors) == 1:
                name_parts = self.authors[0].split()
                if len(name_parts) >= 2:
                    parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}.")
                else:
                    parts.append(f"{self.authors[0]}.")
            elif len(self.authors) == 2:
                parts.append(f"{self.authors[0]}, and {self.authors[1]}.")
            else:
                parts.append(f"{self.authors[0]}, et al.")

        if self.title:
            parts.append(f'"{self.title}."')

        if self.journal:
            parts.append(f"*{self.journal}*,")

        if self.volume:
            vol_str = f"vol. {self.volume}"
            if self.issue:
                vol_str += f", no. {self.issue}"
            parts.append(vol_str + ",")

        if self.year:
            parts.append(f"{self.year},")

        if self.pages:
            parts.append(f"pp. {self.pages}.")

        if self.doi:
            parts.append(f"https://doi.org/{self.doi}.")
        elif self.url:
            parts.append(f"{self.url}.")

        return " ".join(parts)

    def to_chicago(self) -> str:
        """
        Menghasilkan kutipan dalam format **Chicago Manual of Style**.

        Format ini populer di bidang sejarah, seni, dan jurnalisme akademik.

        ---
        ### Return
        - **str**: Kutipan dengan gaya Chicago yang sudah diformat dengan benar.

        ---
        ### Contoh
        ```python
        print(citation.to_chicago())
        # Output:
        # Setiawan, Budi, and Galuh A. Insani. "Deep Learning for E-Waste Classification." 
        # *Journal of Sustainable Computing* 12, no. 3 (2025): 45–58. https://doi.org/10.1234/jsusc.2025.003.
        ```
        """
        ...
        parts = []

        if self.authors:
            if len(self.authors) == 1:
                name_parts = self.authors[0].split()
                if len(name_parts) >= 2:
                    parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}.")
                else:
                    parts.append(f"{self.authors[0]}.")
            else:
                parts.append(", ".join(self.authors) + ".")

        if self.title:
            parts.append(f'"{self.title}."')

        if self.journal:
            journal_part = f"*{self.journal}*"
            if self.volume:
                journal_part += f" {self.volume}"
            if self.issue:
                journal_part += f", no. {self.issue}"
            parts.append(journal_part)

        if self.year:
            parts.append(f"({self.year}):")

        if self.pages:
            parts.append(f"{self.pages}.")

        if self.doi:
            parts.append(f"https://doi.org/{self.doi}.")

        return " ".join(parts)

    def to_ieee(self) -> str:
        """
        Menghasilkan kutipan dalam format **IEEE (Institute of Electrical and Electronics Engineers)**.

        Format ini paling sering digunakan untuk publikasi di bidang teknik, 
        sains komputer, dan rekayasa.

        ---
        ### Return
        - **str**: Kutipan IEEE dalam bentuk string.

        ---
        ### Contoh
        ```python
        print(citation.to_ieee())
        # Output:
        # B. Setiawan and G. A. Insani, "Deep Learning for E-Waste Classification," 
        # *Journal of Sustainable Computing*, vol. 12, no. 3, pp. 45-58, 2025, doi: 10.1234/jsusc.2025.003.
        ```
        """
        ...
        parts = []

        if self.authors:
            author_parts = []
            for author in self.authors[:6]:  # IEEE uses up to 6 authors
                name_parts = author.split()
                if len(name_parts) >= 2:
                    initials = ". ".join([n[0] for n in name_parts[:-1]]) + "."
                    author_parts.append(f"{initials} {name_parts[-1]}")
                else:
                    author_parts.append(author)

            if len(self.authors) > 6:
                author_parts.append("et al.")

            parts.append(", ".join(author_parts) + ",")

        if self.title:
            parts.append(f'"{self.title},"')

        if self.journal:
            journal_part = f"*{self.journal}*"
            if self.volume:
                journal_part += f", vol. {self.volume}"
            if self.issue:
                journal_part += f", no. {self.issue}"
            if self.pages:
                journal_part += f", pp. {self.pages}"
            if self.year:
                journal_part += f", {self.year}"
            parts.append(journal_part + ".")

        if self.doi:
            parts.append(f"doi: {self.doi}.")

        return " ".join(parts)

    def to_plain(self) -> str:
        """
        Menghasilkan kutipan sederhana dalam format teks polos.

        Format ini berguna untuk tampilan minimalis atau ketika hasil kutipan 
        akan digunakan di antarmuka pengguna (UI), catatan cepat, atau sistem log.

        ---
        ### Return
        - **str**: Kutipan sederhana berisi informasi dasar seperti penulis, tahun, judul, 
          dan sumber PDF (jika tersedia).

        ---
        ### Contoh
        ```python
        print(citation.to_plain())
        # Output:
        # Budi Setiawan, Galuh A. Insani. (2025). Deep Learning for E-Waste Classification. 
        # Journal of Sustainable Computing. [paper.pdf, p.3]
        ```
        """
        ...
        parts = []

        if self.authors:
            parts.append(", ".join(self.authors))

        if self.year:
            parts.append(f"({self.year})")

        if self.title:
            parts.append(self.title)

        if self.journal:
            parts.append(self.journal)

        if self.pdf_file and self.page_num:
            parts.append(f"[{self.pdf_file}, p.{self.page_num}]")

        return ". ".join(parts)


class CitationManager:
    """Manages citation extraction and formatting."""

    def __init__(self):
        self.citations = {}

    def extract_from_text(self, text: str) -> List[Citation]:
        """
        Extract citation information from text (e.g., from search results).

        Args:
            text: Text containing citation information

        Returns:
            List of Citation objects
        """
        citations = []

        # Try to extract citations from formatted search results
        # This is a simple implementation - can be enhanced
        pattern = r'\*\*(.*?)\*\*\s*\nAuthors?: (.*?)\nYear: (\d{4})?'
        matches = re.findall(pattern, text, re.MULTILINE)

        for match in matches:
            title, authors, year = match
            author_list = [a.strip() for a in authors.split(',')]

            citation = Citation(
                title=title.strip(),
                authors=author_list,
                year=year
            )
            citations.append(citation)

        return citations

    def format_bibliography(self, citations: List[Citation], format_type: str = "apa") -> str:
        """
        Format multiple citations as a bibliography.

        Args:
            citations: List of Citation objects
            format_type: Citation format (apa, mla, chicago, bibtex, ieee)

        Returns:
            Formatted bibliography string
        """
        if not citations:
            return "No citations to format."

        lines = []

        for i, citation in enumerate(citations, 1):
            if format_type.lower() == "bibtex":
                lines.append(citation.to_bibtex(f"ref{i}"))
            elif format_type.lower() == "apa":
                lines.append(citation.to_apa())
            elif format_type.lower() == "mla":
                lines.append(citation.to_mla())
            elif format_type.lower() == "chicago":
                lines.append(citation.to_chicago())
            elif format_type.lower() == "ieee":
                lines.append(f"[{i}] {citation.to_ieee()}")
            else:
                lines.append(citation.to_plain())

            lines.append("")  # Empty line between citations

        return "\n".join(lines)

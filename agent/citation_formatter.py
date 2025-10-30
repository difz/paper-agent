"""
Modul untuk memformat kutipan bibliografis dalam berbagai gaya akademik
(IEEE, APA, MLA, Chicago, dan BibTeX).

Modul ini menyediakan kelas `CitationFormatter` yang berfungsi untuk mengubah
metadata referensi (seperti penulis, judul, tahun, jurnal, dan DOI)
menjadi teks kutipan yang sesuai dengan standar gaya tertentu.  
Selain itu, juga tersedia fungsi pembungkus `format_citation()` sebagai
antarmuka yang lebih ringkas untuk menghasilkan kutipan penuh maupun kutipan singkat (inline).

Contoh penggunaan:
------------------
metadata = {
.     "title": "Deep Learning for E-Waste Classification",
    "authors": ["Budi Setiawan", "Galuh Adi Insani"],
    "year": "2025",
    "journal": "Journal of Sustainable AI Research",
    "doi": "10.1234/jsair.2025.001"
}
print(format_citation(metadata, style="apa", inline=False))
Setiawan, B., & Insani, G. A. (2025). Deep Learning for E-Waste Classification. Journal of Sustainable AI Research. https://doi.org/10.1234/jsair.2025.001
"""
from typing import Dict, List, Optional
import re


class CitationFormatter:
    """
    Kelas utilitas untuk memformat kutipan dan daftar pustaka
    dalam berbagai gaya akademik (IEEE, APA, MLA, Chicago, BibTeX).

    ---
    ### Deskripsi Umum
    Kelas ini menyediakan metode statis yang memungkinkan pengguna
    untuk memformat metadata bibliografi menjadi teks kutipan lengkap
    atau kutipan singkat (inline) sesuai gaya penulisan yang dipilih.

    Fungsi utamanya meliputi:
    1. Pemformatan daftar penulis sesuai gaya sitasi.
    2. Penyusunan kutipan lengkap berdasarkan metadata artikel.
    3. Penyusunan kutipan singkat untuk penggunaan dalam teks.

    ---
    ### Gaya yang Didukung
    - **IEEE**: Digunakan pada publikasi teknik dan komputer.
    - **APA**: Umum untuk ilmu sosial dan psikologi.
    - **MLA**: Populer di bidang sastra dan humaniora.
    - **Chicago**: Banyak digunakan dalam penelitian sejarah dan umum.
    - **BibTeX**: Untuk integrasi dalam dokumen LaTeX.
    """

    @staticmethod
    def format_authors(authors: List[str], max_authors: int = 3, style: str = 'apa') -> str:
        """
        Memformat daftar nama penulis sesuai dengan gaya sitasi yang ditentukan.

        ---
        ### Parameter
        - **authors** (`List[str]`): Daftar nama penulis, misalnya `["Budi Setiawan", "Galuh Insani"]`.
        - **max_authors** (`int`, opsional): Jumlah maksimum penulis yang ditampilkan sebelum disingkat menjadi “et al.”.
        - **style** (`str`, opsional): Jenis gaya penulisan (`'ieee'`, `'apa'`, `'mla'`, `'chicago'`).

        ---
        ### Return
        - **str**: Nama penulis yang sudah diformat sesuai gaya sitasi.

        ---
        ### Catatan
        - IEEE menampilkan inisial depan diikuti nama belakang (mis. *B. Setiawan*).
        - APA menampilkan nama belakang diikuti inisial (mis. *Setiawan, B.*).
        - MLA menampilkan format *Nama Belakang, Nama Depan*.
        - Chicago dapat menampilkan "et al." untuk tiga penulis atau lebih.
        """
        if not authors:
            return "Unknown Author"

        if style == 'ieee':
            # IEEE: First Initial. Last Name
            formatted = []
            for author in authors[:max_authors]:
                parts = author.strip().split()
                if len(parts) >= 2:
                    first_initial = parts[0][0] + '.'
                    last_name = ' '.join(parts[1:])
                    formatted.append(f"{first_initial} {last_name}")
                else:
                    formatted.append(author)

            if len(authors) > max_authors:
                return ', '.join(formatted) + ', et al.'
            return ' and '.join(formatted) if len(formatted) <= 2 else ', '.join(formatted[:-1]) + ', and ' + formatted[-1]

        elif style == 'apa':
            # APA: Last, F. M.
            formatted = []
            for author in authors[:max_authors]:
                parts = author.strip().split()
                if len(parts) >= 2:
                    last_name = parts[-1]
                    initials = '. '.join([p[0] for p in parts[:-1]]) + '.'
                    formatted.append(f"{last_name}, {initials}")
                else:
                    formatted.append(author)

            if len(authors) > max_authors:
                return ', '.join(formatted) + ', et al.'
            return ', & '.join(formatted) if len(formatted) == 2 else ', '.join(formatted[:-1]) + ', & ' + formatted[-1] if len(formatted) > 2 else formatted[0]

        elif style == 'mla':
            # MLA: Last, First
            if authors:
                parts = authors[0].strip().split()
                if len(parts) >= 2:
                    first = ' '.join(parts[:-1])
                    last = parts[-1]
                    result = f"{last}, {first}"
                else:
                    result = authors[0]

                if len(authors) > 1:
                    result += ", et al."
                return result
            return "Unknown Author"

        elif style == 'chicago':
            # Chicago: First Last
            if len(authors) == 1:
                return authors[0]
            elif len(authors) == 2:
                return f"{authors[0]} and {authors[1]}"
            elif len(authors) > 2:
                return f"{authors[0]} et al."

        return ', '.join(authors[:max_authors])

    @staticmethod
    def format_citation(metadata: Dict, page: Optional[int] = None, style: str = 'ieee') -> str:
        """
        Membentuk kutipan lengkap berdasarkan metadata bibliografi.

        ---
        ### Parameter
        - **metadata** (`Dict`): Metadata bibliografi (judul, penulis, tahun, jurnal, DOI, dll.).
        - **page** (`int`, opsional): Nomor halaman spesifik yang ingin dicantumkan.
        - **style** (`str`, opsional): Jenis format kutipan (`'ieee'`, `'apa'`, `'mla'`, `'chicago'`, `'bibtex'`).

        ---
        ### Return
        - **str**: Kutipan lengkap yang diformat sesuai gaya akademik yang dipilih.

        ---
        ### Contoh
        ```python
        metadata = {
            "title": "E-Waste Sorting with AI",
            "authors": ["Budi Setiawan", "Galuh A. Insani"],
            "year": "2025",
            "journal": "AI & Sustainability",
            "doi": "10.5678/ais.2025.77"
        }
        CitationFormatter.format_citation(metadata, style="ieee")
        ```
        """
        authors = metadata.get('authors', [])
        title = metadata.get('title', metadata.get('filename', 'Unknown Title'))
        year = metadata.get('year', 'n.d.')
        journal = metadata.get('journal', None)
        doi = metadata.get('doi', None)

        if style == 'ieee':
            # IEEE: [1] F. Author, "Title," Journal, vol. X, no. Y, pp. Z-Z, Year.
            author_str = CitationFormatter.format_authors(authors, max_authors=3, style='ieee')
            citation = f'{author_str}, "{title}"'

            if journal:
                citation += f', {journal}'

            if year:
                citation += f', {year}'

            if page:
                citation += f', p. {page}'

            if doi:
                citation += f', doi: {doi}'

            return citation + '.'

        elif style == 'apa':
            # APA: Author, A. A. (Year). Title. Journal, vol(issue), pages. DOI
            author_str = CitationFormatter.format_authors(authors, max_authors=7, style='apa')
            citation = f'{author_str} ({year}). {title}.'

            if journal:
                citation += f' {journal}.'

            if page:
                citation += f' p. {page}.'

            if doi:
                citation += f' https://doi.org/{doi}'

            return citation

        elif style == 'mla':
            # MLA: Last, First. "Title." Journal, Year, pages.
            author_str = CitationFormatter.format_authors(authors, max_authors=1, style='mla')
            citation = f'{author_str}. "{title}."'

            if journal:
                citation += f' {journal},'

            citation += f' {year}'

            if page:
                citation += f', p. {page}'

            return citation + '.'

        elif style == 'chicago':
            # Chicago: Author. "Title." Journal (Year): pages.
            author_str = CitationFormatter.format_authors(authors, max_authors=3, style='chicago')
            citation = f'{author_str}. "{title}."'

            if journal:
                citation += f' {journal}'

            citation += f' ({year})'

            if page:
                citation += f': {page}'

            return citation + '.'

        elif style == 'bibtex':
            # BibTeX format
            # Generate a citation key
            author_last = authors[0].split()[-1] if authors else 'unknown'
            key = f'{author_last.lower()}{year}'

            bibtex = f'@article{{{key},\n'
            bibtex += f'  author = {{{" and ".join(authors)}}},\n'
            bibtex += f'  title = {{{title}}},\n'

            if journal:
                bibtex += f'  journal = {{{journal}}},\n'

            bibtex += f'  year = {{{year}}},\n'

            if page:
                bibtex += f'  pages = {{{page}}},\n'

            if doi:
                bibtex += f'  doi = {{{doi}}},\n'

            bibtex += '}'
            return bibtex

        # Default simple format
        author_str = ', '.join(authors) if authors else 'Unknown'
        citation = f'{author_str}. {title}. {year}'
        if page:
            citation += f', p. {page}'
        return citation

    @staticmethod
    def format_inline_citation(metadata: Dict, page: Optional[int] = None, style: str = 'ieee') -> str:
        """
        Membentuk kutipan singkat (inline) yang digunakan di dalam teks.

        ---
        ### Parameter
        - **metadata** (`Dict`): Metadata kutipan (mis. nama penulis dan tahun).
        - **page** (`int`, opsional): Nomor halaman.
        - **style** (`str`, opsional): Gaya sitasi (`'ieee'`, `'apa'`, `'mla'`, `'chicago'`).

        ---
        ### Return
        - **str**: Kutipan pendek dalam bentuk teks, misalnya `(Setiawan, 2025, p. 10)`.

        ---
        ### Catatan
        Kutipan ini biasa digunakan dalam teks utama (in-text citation)
        untuk merujuk sumber tanpa menampilkan detail lengkap.
        """
        authors = metadata.get('authors', [])
        year = metadata.get('year', 'n.d.')

        if style == 'ieee':
            # IEEE uses numbered references [1], [2], etc.
            # For inline, we'll use author-year for clarity
            author_last = authors[0].split()[-1] if authors else 'Unknown'
            citation = f'({author_last}, {year}'
            if page:
                citation += f', p. {page}'
            return citation + ')'

        elif style == 'apa':
            # APA: (Author, Year, p. X)
            if authors:
                author_last = authors[0].split()[-1] if authors else 'Unknown'
                if len(authors) == 2:
                    author_last2 = authors[1].split()[-1]
                    author_str = f'{author_last} & {author_last2}'
                elif len(authors) > 2:
                    author_str = f'{author_last} et al.'
                else:
                    author_str = author_last
            else:
                author_str = 'Unknown'

            citation = f'({author_str}, {year}'
            if page:
                citation += f', p. {page}'
            return citation + ')'

        elif style == 'mla':
            # MLA: (Author Page)
            author_last = authors[0].split()[-1] if authors else 'Unknown'
            if page:
                return f'({author_last} {page})'
            return f'({author_last})'

        elif style == 'chicago':
            # Chicago: (Author Year, Page)
            author_last = authors[0].split()[-1] if authors else 'Unknown'
            citation = f'({author_last} {year}'
            if page:
                citation += f', {page}'
            return citation + ')'

        # Default
        author_last = authors[0].split()[-1] if authors else 'Unknown'
        citation = f'({author_last}, {year}'
        if page:
            citation += f', p. {page}'
        return citation + ')'


def format_citation(metadata: Dict, page: Optional[int] = None, style: str = 'ieee', inline: bool = True) -> str:
    """
    Fungsi pembungkus untuk memformat kutipan dengan cepat.

    ---
    ### Deskripsi
    Fungsi ini menyediakan antarmuka sederhana untuk memanggil
    `CitationFormatter`. Berguna untuk menghasilkan kutipan
    penuh (bibliografi) atau kutipan singkat (inline)
    tanpa harus membuat instance kelas.

    ---
    ### Parameter
    - **metadata** (`Dict`): Metadata bibliografi.
    - **page** (`int`, opsional): Nomor halaman.
    - **style** (`str`, opsional): Jenis gaya kutipan.
    - **inline** (`bool`, opsional):  
      Jika `True`, menghasilkan kutipan singkat (mis. `(Setiawan, 2025)`);  
      Jika `False`, menghasilkan kutipan lengkap.

    ---
    ### Return
    - **str**: Teks kutipan yang diformat.

    ---
    ### Contoh
    ```python
    metadata = {"title": "Smart Recycling", "authors": ["Budi Setiawan"], "year": "2025"}
    print(format_citation(metadata, style="apa", inline=True))
    # Output: (Setiawan, 2025)
    ```
    """
    formatter = CitationFormatter()
    if inline:
        return formatter.format_inline_citation(metadata, page, style)
    else:
        return formatter.format_citation(metadata, page, style)

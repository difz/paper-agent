"""
Test script to debug PDF metadata extraction.
Run this to see what metadata is being extracted from your PDFs.
"""
import sys
from agent.pdf_metadata import extract_pdf_metadata
from rich.console import Console
from rich.table import Table
import glob

console = Console()

def test_pdf_extraction(pdf_path: str):
    """Test metadata extraction on a single PDF."""
    console.print(f"\n[bold cyan]Testing: {pdf_path}[/bold cyan]")
    console.print("=" * 80)

    metadata = extract_pdf_metadata(pdf_path)

    table = Table(title="Extracted Metadata")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Filename", str(metadata.get('filename', 'N/A')))
    table.add_row("Title", str(metadata.get('title', 'N/A')))
    table.add_row("Authors", ', '.join(metadata.get('authors', [])) or 'N/A')
    table.add_row("Year", str(metadata.get('year', 'N/A')))
    table.add_row("Journal", str(metadata.get('journal', 'N/A')))
    table.add_row("DOI", str(metadata.get('doi', 'N/A')))

    console.print(table)

    # Show first page text snippet
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        if len(reader.pages) > 0:
            first_page = reader.pages[0].extract_text()
            console.print("\n[bold yellow]First 1000 characters of first page:[/bold yellow]")
            console.print(first_page[:1000])
            console.print("...")
    except Exception as e:
        console.print(f"[red]Error reading PDF: {e}[/red]")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific PDF
        pdf_path = sys.argv[1]
        test_pdf_extraction(pdf_path)
    else:
        # Test all PDFs in corpus
        console.print("[bold]Testing all PDFs in ./corpus[/bold]\n")
        pdfs = glob.glob("./corpus/*.pdf")

        if not pdfs:
            console.print("[yellow]No PDFs found in ./corpus[/yellow]")
            console.print("\nUsage: python test_metadata_extraction.py <path_to_pdf>")
        else:
            for pdf in pdfs:
                test_pdf_extraction(pdf)
                console.print("\n")

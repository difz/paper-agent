"""
Document summarization system for generating automatic summaries of PDFs.
Creates structured summaries with key findings, methodology, and conclusions.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .config import Settings

log = logging.getLogger("document_summarizer")


class DocumentSummarizer:
    """Generates and manages document summaries."""

    def __init__(self, summary_dir: str = "./store/summaries"):
        self.summary_dir = Path(summary_dir)
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        self.settings = Settings()
        self.llm = ChatGoogleGenerativeAI(model=self.settings.llm_model, temperature=0)

    def _get_summary_file(self, pdf_filename: str) -> Path:
        """Get the summary file path for a PDF."""
        # Use sanitized filename as base
        safe_name = "".join(c for c in pdf_filename if c.isalnum() or c in "._- ")
        summary_file = self.summary_dir / f"{safe_name}.json"
        return summary_file

    def generate_summary(self, pdf_path: str) -> Dict:
        """
        Generate a comprehensive summary of a PDF document.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing summary components
        """
        log.info(f"Generating summary for: {pdf_path}")

        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()

            if not pages:
                return {"error": "No content extracted from PDF"}

            # Extract text from first few pages (for abstract/intro)
            intro_text = "\n\n".join([p.page_content for p in pages[:3]])

            # Extract text from middle pages (for methodology)
            mid_start = len(pages) // 3
            mid_end = 2 * len(pages) // 3
            method_text = "\n\n".join([p.page_content for p in pages[mid_start:mid_end][:3]])

            # Extract text from last few pages (for conclusions)
            conclusion_text = "\n\n".join([p.page_content for p in pages[-3:]])

            # Generate overview summary
            overview = self._generate_overview(intro_text)

            # Generate key findings
            findings = self._extract_key_findings("\n\n".join([p.page_content for p in pages]))

            # Extract methodology (if applicable)
            methodology = self._extract_methodology(method_text)

            # Generate conclusions
            conclusions = self._extract_conclusions(conclusion_text)

            # Extract metadata
            metadata = self._extract_metadata(intro_text, pages[0].metadata)

            summary = {
                "filename": Path(pdf_path).name,
                "total_pages": len(pages),
                "metadata": metadata,
                "overview": overview,
                "key_findings": findings,
                "methodology": methodology,
                "conclusions": conclusions,
                "generated_at": pages[0].metadata.get("source", "")
            }

            # Save summary
            self._save_summary(Path(pdf_path).name, summary)

            return summary

        except Exception as e:
            log.error(f"Error generating summary: {e}", exc_info=True)
            return {"error": str(e)}

    def _generate_overview(self, text: str) -> str:
        """Generate a brief overview from the introduction."""
        prompt = ChatPromptTemplate.from_template(
            """You are a research assistant. Read the following text from the beginning of a research paper and provide a brief 2-3 sentence overview of what the paper is about.

TEXT:
{text}

Provide a clear, concise overview:"""
        )

        try:
            chain = prompt | self.llm
            result = chain.invoke({"text": text[:4000]})  # Limit text length
            return result.content.strip()
        except Exception as e:
            log.error(f"Error generating overview: {e}")
            return "Overview generation failed."

    def _extract_key_findings(self, text: str) -> List[str]:
        """Extract key findings from the document."""
        prompt = ChatPromptTemplate.from_template(
            """You are a research assistant. Read the following research paper text and extract 3-5 key findings or main points.

TEXT:
{text}

Provide key findings as a bulleted list (use - for bullets):"""
        )

        try:
            # Sample text if too long
            sample_text = text[:8000] if len(text) > 8000 else text

            chain = prompt | self.llm
            result = chain.invoke({"text": sample_text})

            # Parse bullet points
            findings = [
                line.strip().lstrip('-').strip()
                for line in result.content.split('\n')
                if line.strip() and (line.strip().startswith('-') or line.strip().startswith('*'))
            ]

            return findings[:5] if findings else ["Key findings extraction in progress."]

        except Exception as e:
            log.error(f"Error extracting findings: {e}")
            return ["Key findings extraction failed."]

    def _extract_methodology(self, text: str) -> str:
        """Extract methodology description."""
        prompt = ChatPromptTemplate.from_template(
            """You are a research assistant. Read the following text and briefly describe the research methodology used (if any). If no clear methodology is present, say "Not applicable" or "Not a research paper".

TEXT:
{text}

Methodology (1-2 sentences):"""
        )

        try:
            chain = prompt | self.llm
            result = chain.invoke({"text": text[:4000]})
            return result.content.strip()
        except Exception as e:
            log.error(f"Error extracting methodology: {e}")
            return "Methodology extraction failed."

    def _extract_conclusions(self, text: str) -> str:
        """Extract conclusions from the document."""
        prompt = ChatPromptTemplate.from_template(
            """You are a research assistant. Read the following text from the end of a paper and summarize the main conclusions in 2-3 sentences.

TEXT:
{text}

Conclusions:"""
        )

        try:
            chain = prompt | self.llm
            result = chain.invoke({"text": text[:4000]})
            return result.content.strip()
        except Exception as e:
            log.error(f"Error extracting conclusions: {e}")
            return "Conclusions extraction failed."

    def _extract_metadata(self, text: str, pdf_metadata: Dict) -> Dict:
        """Extract document metadata."""
        metadata = {
            "title": "Unknown",
            "authors": [],
            "year": None
        }

        # Try to extract from first page text
        lines = text.split('\n')[:20]  # First 20 lines

        # Simple heuristic: title is often the first non-empty line
        for line in lines:
            if line.strip() and len(line.strip()) > 10:
                metadata["title"] = line.strip()
                break

        return metadata

    def _save_summary(self, pdf_filename: str, summary: Dict):
        """Save summary to file."""
        summary_file = self._get_summary_file(pdf_filename)

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        log.info(f"Saved summary to: {summary_file}")

    def get_summary(self, pdf_filename: str) -> Optional[Dict]:
        """Retrieve existing summary for a PDF."""
        summary_file = self._get_summary_file(pdf_filename)

        if not summary_file.exists():
            return None

        with open(summary_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def format_summary_for_display(self, summary: Dict) -> str:
        """Format summary for Discord display."""
        if "error" in summary:
            return f"❌ Error: {summary['error']}"

        lines = [
            f"📄 **{summary.get('filename', 'Document Summary')}**",
            f"📊 Pages: {summary.get('total_pages', 'N/A')}",
            "",
            "**📝 Overview:**",
            summary.get('overview', 'N/A'),
            "",
            "**🔍 Key Findings:**"
        ]

        findings = summary.get('key_findings', [])
        for finding in findings:
            lines.append(f"  • {finding}")

        lines.extend([
            "",
            "**🔬 Methodology:**",
            summary.get('methodology', 'N/A'),
            "",
            "**💡 Conclusions:**",
            summary.get('conclusions', 'N/A')
        ])

        return "\n".join(lines)

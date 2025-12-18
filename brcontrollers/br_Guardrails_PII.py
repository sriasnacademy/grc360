import os
from faker import Faker
from PyPDF2 import PdfReader
from docx import Document

from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern

class PIIService:
    def __init__(self):
        self.fake = Faker()
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self._register_custom_patterns()

    def _register_custom_patterns(self):
        polish_id_pattern = Pattern(
            name="polish_id_pattern",
            regex="[A-Z]{3}\d{6}",
            score=1,
        )

        time_pattern = Pattern(
            name="time_pattern",
            regex="(1[0-2]|0?[1-9]):[0-5][0-9] (AM|PM)",
            score=1,
        )

        polish_id_recognizer = PatternRecognizer(
            supported_entity="POLISH_ID",
            patterns=[polish_id_pattern]
        )

        time_recognizer = PatternRecognizer(
            supported_entity="TIME",
            patterns=[time_pattern]
        )

        self.analyzer.registry.add_recognizer(polish_id_recognizer)
        self.analyzer.registry.add_recognizer(time_recognizer)

    def read_file(self, file_path: str) -> str:   
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()

        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif ext == ".docx":
            try:
                from docx import Document
            except ImportError:
                raise Exception("python-docx not installed")

            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        else:
            raise Exception("Unsupported file format")
  

    def anonymize_text(self, text: str) -> str:
        analyzer_results = self.analyzer.analyze(
            text=text,
            language="en"
        )

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results
        )

        return anonymized.text

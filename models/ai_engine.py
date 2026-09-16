from utils.chemical_loader import load_all_chemicals
from utils.knowledge_base import KNOWLEDGE
from utils.response_formatter import (
    format_chemical,
    format_green_chemistry,
    format_lab_safety,
)
from utils.gemini_service import ask_gemini, ask_gemini_stream
from utils.smart_cache import get_cached_answer, save_answer

FORMATTERS = {
    "green_chemistry": format_green_chemistry,
    "lab_safety": format_lab_safety,
}


class AIEngine:

    def __init__(self):
        self.chemicals = load_all_chemicals()

    def normalize(self, text):
        return (
            text.lower()
            .replace("₀", "0")
            .replace("₁", "1")
            .replace("₂", "2")
            .replace("₃", "3")
            .replace("₄", "4")
            .replace("₅", "5")
            .replace("₆", "6")
            .replace("₇", "7")
            .replace("₈", "8")
            .replace("₉", "9")
            .strip()
        )

    def find_local_match(self, question):

        # Knowledge Base
        for topic in KNOWLEDGE.values():
            for keyword in topic["keywords"]:
                if keyword in question:
                    formatter = FORMATTERS.get(topic["formatter"])
                    if formatter:
                        return formatter(topic), None

        # Chemical Database
        for chemical in self.chemicals:

            name = chemical.get("name", "").lower()
            formula = chemical.get("formula", "").lower()
            aliases = [a.lower() for a in chemical.get("aliases", [])]

            context = f"""
Name: {chemical.get('name')}
Formula: {chemical.get('formula')}
Category: {chemical.get('category')}
Description: {chemical.get('description')}
Hazards: {chemical.get('hazards')}
Storage: {chemical.get('storage')}
Disposal: {chemical.get('disposal')}
Green Alternative: {chemical.get('green_alternative')}
"""

            if name and name in question:
                return format_chemical(chemical), None

            if formula and formula in question:
                return None, context

            for alias in aliases:
                if alias in question:
                    return None, context

            for word in name.split():
                if len(word) > 3 and word in question:
                    return None, context

        return None, None

    def get_response(self, question):

        question = self.normalize(question)

        # Persistent six-month cache: repeated questions are answered locally
        # without contacting Gemini, even after restart or API-key changes.
        cached_answer = get_cached_answer(question)
        if cached_answer:
            return cached_answer

        local_answer, context = self.find_local_match(question)

        if local_answer:
            return local_answer

        answer = ask_gemini(question, context)
        save_answer(question, answer)
        return answer

    def get_response_stream(self, question):

        question = self.normalize(question)

        cached_answer = get_cached_answer(question)
        if cached_answer:
            yield cached_answer
            return

        local_answer, context = self.find_local_match(question)

        if local_answer:
            yield local_answer
            return

        full_answer = ""
        for chunk in ask_gemini_stream(question, context):
            full_answer += chunk
            yield chunk
        save_answer(question, full_answer)

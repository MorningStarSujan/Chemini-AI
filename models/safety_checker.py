import json
import os


class SafetyChecker:
    """Handles loading and searching laboratory safety rules."""

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.rules_file = os.path.join(base_dir, "data", "safety_rules.json")

    def get_all_rules(self):
        """Return all safety rules."""
        try:
            with open(self.rules_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def get_rule_by_id(self, rule_id):
        """Return a single safety rule by ID."""
        rules = self.get_all_rules()

        for rule in rules:
            if rule.get("id") == rule_id:
                return rule

        return None

    def search_rules(self, keyword):
        """Search safety rules by title, category, or description."""
        keyword = keyword.lower()

        results = []

        for rule in self.get_all_rules():
            if (
                keyword in rule.get("title", "").lower()
                or keyword in rule.get("category", "").lower()
                or keyword in rule.get("description", "").lower()
            ):
                results.append(rule)

        return results

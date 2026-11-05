from typing import Any

from lingora.modules.learning.contracts import LessonDraft, reading_prefix
from lingora.modules.learning.provider import Generated


def lesson_data() -> dict[str, Any]:
    return {
        "title": "A small garden for the community",
        "objectives": ["Find a key fact in a short report.", "Use words about community projects."],
        "reading": (
            "A local community is planning a garden. The garden will open in June. Volunteers "
            "will plant trees and flowers. The project gives neighbours a place to meet. "
            "Imagine that you are a volunteer. You could help to plant a tree or bring some "
            "water. This example shows how people can work together. A small action can help "
            "a shared space grow."
        ),
        "vocabulary": [
            {"term": "garden", "meaning": "A place for growing plants."},
            {"term": "volunteer", "meaning": "A person who helps without payment."},
            {"term": "project", "meaning": "A planned piece of work."},
        ],
        "exercises": [
            {
                "kind": "choice",
                "prompt": "What are people planning?",
                "options": ["A garden", "A library", "A station"],
                "parts": [],
                "skill": "Reading: identify the main idea",
                "correct_answers": ["A garden"],
                "explanation": "The first sentence says people are planning a garden.",
                "evidence": "A local community is planning a garden.",
            },
            {
                "kind": "gap",
                "prompt": "Volunteers will ___ trees.",
                "options": [],
                "parts": [],
                "skill": "Vocabulary: use a verb",
                "correct_answers": ["plant"],
                "explanation": "The verb plant means to put a plant into the ground.",
                "evidence": "Volunteers will plant trees and flowers.",
            },
            {
                "kind": "matching",
                "prompt": "Match the words with their meanings.",
                "options": ["A planned piece of work", "A person who helps"],
                "parts": ["volunteer", "project"],
                "skill": "Vocabulary: connect word meanings",
                "correct_answers": ["A person who helps", "A planned piece of work"],
                "explanation": "A volunteer helps; a project is a planned activity.",
                "evidence": "",
            },
            {
                "kind": "comprehension",
                "prompt": "In which month will the garden open?",
                "options": [],
                "parts": [],
                "skill": "Reading: locate a time",
                "correct_answers": ["June"],
                "explanation": "The second sentence states that the garden will open in June.",
                "evidence": "The garden will open in June.",
            },
            {
                "kind": "short_answer",
                "prompt": "Complete the phrase: a place to ___.",
                "options": [],
                "parts": [],
                "skill": "Reading: find a verb",
                "correct_answers": ["meet"],
                "explanation": "The text describes a place where neighbours can meet.",
                "evidence": "The project gives neighbours a place to meet.",
            },
        ],
        "discussion": [
            "Would you like a garden near your home? Why?",
            "How could you help a community project?",
        ],
    }


class FakeProvider:
    calls = 0

    async def generate(self, context: dict[str, Any]) -> Generated:
        self.calls += 1
        data = lesson_data()
        data["reading"] = reading_prefix(context) + data["reading"]
        return Generated(LessonDraft.model_validate(data), "test-model", 100, 200)

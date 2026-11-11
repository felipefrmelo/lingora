"""Fixed feedback phrases used when the learner has disabled short examples."""

SUMMARIES = (
    "You practised discussing the lesson.",
    "You practised expressing ideas about the lesson.",
    "You practised responding to questions about the lesson.",
)

STRENGTHS = (
    "You expressed ideas clearly.",
    "You used relevant vocabulary.",
    "You supported ideas with reasons.",
    "You responded to the discussion prompts.",
    "You used complete sentences.",
    "You participated in the conversation.",
)

PRIORITIES = (
    "Practise subject–verb agreement.",
    "Practise using verb tenses consistently.",
    "Practise using articles and prepositions.",
    "Practise expanding answers with reasons.",
    "Practise using vocabulary from the lesson.",
    "Practise connecting ideas in longer sentences.",
)


def options() -> dict[str, list[str]]:
    return {
        "summaries": list(SUMMARIES),
        "strengths": list(STRENGTHS),
        "priorities": list(PRIORITIES),
    }

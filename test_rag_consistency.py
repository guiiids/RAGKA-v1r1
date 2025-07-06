import pytest
from rag_assistant_with_history_copy import FlaskRAGAssistantWithHistory

initial_prompt = """A user complains that they get no final libraries on their Magnis instrument despite following the manual precisely. Which questions should I, an Agilent remote engineer, ask to probe how they prepared the samples?"""

followup_prompt = "No sample preparation issues were discovered. What could be the next steps?"

initial_required = [
    "To investigate why the user is getting no final libraries",
    "### 1. Input DNA/RNA Preparation",
    "### 2. Reagent Handling",
    "### 3. Deck Setup",
]

followup_required = [
    "If no sample preparation issues were discovered and an engineer is required to go on-site",
    "### 1. Review Site Preparation",
    "### 2. Inspect Instrument Setup",
    "### 3. Check Instrument Components",
]

def test_rag_consistency():
    assistant = FlaskRAGAssistantWithHistory()
    answers_initial = []
    answers_followup = []

    for _ in range(5):
        a1, _, _, _, _ = assistant.generate_rag_response(initial_prompt)
        answers_initial.append(a1)
        a2, _, _, _, _ = assistant.generate_rag_response(followup_prompt)
        answers_followup.append(a2)

    # Ensure we received exactly 5 responses
    assert len(answers_initial) == 5, "Did not collect 5 initial responses"
    assert len(answers_followup) == 5, "Did not collect 5 follow-up responses"

    # Check required content appears in each response
    for resp in answers_initial:
        for phrase in initial_required:
            assert phrase in resp

    for resp in answers_followup:
        for phrase in followup_required:
            assert phrase in resp
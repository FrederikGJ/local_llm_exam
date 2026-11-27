"""Temporary stand-in for the real answer function (LLM-9).

The real function must have the same name and signature:
answer_question(question: str) -> str, returning the answer as Markdown
that ends with the Sources: list.
"""

import time


FAKE_ANSWER = """A CPR number (Personal Registration Number) is Denmark's unique identifier for residents. [Source 1]

To get one (if you plan to stay in Denmark for more than 3 months):
1. Visit an International Citizen Service office in Aalborg, Aarhus, Odense, or Copenhagen.
2. OR go to your local Borgerservice (municipal Citizen Service Centre).
3. Choose a doctor at registration.
4. You'll receive a social security card (sundhedskort) by post within 2 weeks – it includes your CPR number. [Source 1]

Sources:
- [Source 1] Welcome to Denmark — Workindenmark (https://www.workindenmark.dk/)
"""


def answer_question(question: str) -> str:
    time.sleep(2)
    return FAKE_ANSWER

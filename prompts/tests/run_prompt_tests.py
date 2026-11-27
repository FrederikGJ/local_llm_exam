"""Ask two local models a legit and an off-topic question using the 4T system prompt."""

import json
from pathlib import Path
from urllib.request import Request, urlopen


SYSTEM_PROMPT = (Path(__file__).resolve().parents[1] / "system_prompt.txt").read_text(encoding="utf-8")

MODELS = {
    "default": "qwen:0.5b-chat-v1.5-q2_K",
    "qwen3": "qwen3:4b",
}

QUESTIONS = {
    "legit": "What is a CPR number and how do I get one?",
    "offtopic": "Who won the US midterm elections?",
}

# Hand-picked excerpt from viden_bibliotek/ (stands in for retrieval, which is not built yet).
SOURCES = (
    "[Source 1] Welcome to Denmark — Workindenmark\n"
    "Link: https://www.workindenmark.dk/\n"
    "If you are planning to stay in Denmark for more than 3 months, you can register for a "
    "Personal Registration Number (CPR number) and a health card. You can apply for a CPR number "
    "and a health card at the International Citizen Service in Aalborg, Aarhus, Odense or Copenhagen "
    "or at the local municipal Citizen Service Centre (Danish: Borgerservice). At the registration "
    "you will choose a doctor. Your social security card (Danish: sundhedskort) which includes your "
    "CPR number will be send to you by post – normally within 2 weeks."
)


def ask(model: str, question: str) -> str:
    body = {
        "model": model,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 4096},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Sources:\n{SOURCES}\n\nQuestion: {question}"},
        ],
    }
    request = Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=900) as response:
        return json.load(response)["message"]["content"]


responses = {}
for model_name, model in MODELS.items():
    for question_name, question in QUESTIONS.items():
        print(f"Asking {model}: {question}", flush=True)
        responses[f"{question_name}_{model_name}"] = ask(model, question)

for label, answer in responses.items():
    print(f"\n===== {label}\n{answer}")

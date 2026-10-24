"""宿題（基礎）: 同じ質問を3回ずつ、モデルと temperature を変えて比べる。

    PYTHONPATH=. uv run python lectures/01/compare.py
"""

import time

from google.genai import errors

from app.ask import generate

QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
CONDITIONS = [
    ("gemini-3.5-flash-lite", None),
    ("gemini-3.5-flash", None),
    ("gemini-3.5-flash-lite", 0.0),
    ("gemini-3.5-flash-lite", 1.5),
]
TRIES = 3


def generate_retry(question, model, temperature):
    for _ in range(3):
        try:
            return generate(question, model=model, temperature=temperature)
        except errors.ServerError:  # 503（混雑）は少し待てば通ることが多い
            time.sleep(20)
    return generate(question, model=model, temperature=temperature)


print(f"質問: {QUESTION}\n")
print("| モデル | temperature | 回 | 出力トークン | 回答の書き出し |")
print("|---|---|---|---|---|")
for model, temperature in CONDITIONS:
    for i in range(1, TRIES + 1):
        r = generate_retry(QUESTION, model, temperature)
        head = " ".join(r.text.split())[:60]
        t = "既定" if temperature is None else temperature
        print(f"| {model} | {t} | {i} | {r.usage_metadata.candidates_token_count} | {head} |")
        time.sleep(6)  # 無料枠のレート制限よけ

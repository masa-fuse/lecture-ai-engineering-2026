"""第5回 宿題（基礎）：検索件数 RAG_TOP_K を 5 → 2 にして、同じ質問で比べる。

uv run python lectures/05/compare.py   （PYTHONPATH=. が要る）
"""
import json
import re
import time
from pathlib import Path
from time import perf_counter

from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ToolCallPart, ToolReturnPart

from app import retrieval
from app.agent import agent, build_model

QUESTIONS = {
    "lora": "第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？",
    "memory": "第3回の例では、コンパクションとセッションをまたぐメモリはどう違いますか。日々のメモはすべて長期メモリに入りますか",
}
TOP_KS = [5, 2]
TRIES = 2


def ask(question, top_k):
    retrieval.RAG_TOP_K = top_k
    for wait in (0, 30, 60, 120):
        time.sleep(wait)
        try:
            started = perf_counter()
            result = agent.run_sync(question, model=build_model())
            break
        except ModelHTTPError as e:
            if e.status_code not in (429, 503):
                raise
    seconds = perf_counter() - started
    queries, pages = [], []
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                queries.append(part.args_as_dict().get("query"))
            elif isinstance(part, ToolReturnPart) and part.tool_name == "search_materials":
                pages.append([r["page_id"] for r in json.loads(part.content).get("results", [])])
    cited = set()  # 「第3回・PDF p.39, p.40」のように1つの回にページが並ぶ書き方も拾う
    for m in re.finditer(r"第(\d)回・PDF ((?:p\.\s*\d+[、,，\s]*)+)", result.output):
        cited |= {(int(m.group(1)), int(x)) for x in re.findall(r"p\.\s*(\d+)", m.group(2))}
    cited = sorted(cited)
    return {
        "top_k": top_k, "queries": queries, "pages": pages,
        "cited": [f"{a}-{b}" for a, b in cited], "seconds": round(seconds, 2),
        "input_tokens": result.usage.input_tokens, "output_tokens": result.usage.output_tokens,
        "requests": result.usage.requests, "cost": float(result.usage.cost) if result.usage.cost is not None else None, "answer": result.output,
    }


rows = []
for name, question in QUESTIONS.items():
    for top_k in TOP_KS:
        for n in range(1, TRIES + 1):
            r = {"question": name, "try": n, **ask(question, top_k)}
            rows.append(r)
            print(f"{name} k={top_k} {n}回目: 検索{len(r['queries'])}回 {r['queries']}  引用 {r['cited']}  "
                  f"{r['seconds']}秒  入力{r['input_tokens']:,}  応答{r['requests']}回  ${r['cost'] or 0:.6f}", flush=True)

Path(__file__).with_name("compare_result.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

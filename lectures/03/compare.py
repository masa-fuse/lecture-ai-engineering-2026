"""宿題（基礎）: 指示（INSTRUCTIONS）とツールの説明文（docstring）を1か所ずつ変えて、同じ質問で比べる。

    PYTHONPATH=. uv run python lectures/03/compare.py
"""

import time

from pydantic_ai import Agent, Tool
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ToolCallPart

from app import tools
from app.agent import INSTRUCTIONS, build_model

QUESTIONS = [
    "LoRAとQLoRAの違いは？",
    "AIE2026の講座の宿題にある「3レベル」とは何ですか？",
    "RAGとファインチューニングはどう使い分ける？",
]
TRIES = 2

SEARCH_DOC = tools.search_glossary.__doc__
ONE_TERM = "query には調べたい用語を1つだけ入れる（例: \"LoRA\"）。"
MANY_TERMS = "query には調べたい用語をまとめて入れる（例: \"LoRA QLoRA\"）。"
MUST_SEARCH = "- 用語や講座に固有のことを答える前に、必ず search_glossary で用語集を確認する。\n"


def build_agent(instructions=INSTRUCTIONS, search_doc=SEARCH_DOC):
    return Agent(
        instructions=instructions,
        tools=[
            Tool(tools.search_glossary, description=search_doc),
            tools.get_lecture_summary,
            tools.make_quiz,
        ],
    )


CONDITIONS = {
    "元のまま": build_agent(),
    "「必ず検索」の行を消す": build_agent(instructions=INSTRUCTIONS.replace(MUST_SEARCH, "")),
    "docstring を「まとめて入れる」に": build_agent(search_doc=SEARCH_DOC.replace(ONE_TERM, MANY_TERMS)),
}


def run(agent, question):
    for _ in range(3):
        try:
            return agent.run_sync(question, model=build_model())
        except ModelHTTPError as e:
            if e.status_code not in (429, 503):
                raise
            time.sleep(20)  # 混雑・レート制限は少し待てば通ることが多い
    return agent.run_sync(question, model=build_model())


def calls(result):
    return [
        f"{p.tool_name}({p.args_as_dict()})"
        for m in result.all_messages() for p in m.parts if isinstance(p, ToolCallPart)
    ]


print("| 条件 | 質問 | 回 | requests | ツール呼び出し | 回答の書き出し |")
print("|---|---|---|---|---|---|")
answers = []
for name, agent in CONDITIONS.items():
    for q in QUESTIONS:
        for i in range(1, TRIES + 1):
            r = run(agent, q)
            head = " ".join(r.output.split())[:50]
            print(f"| {name} | {q[:16]} | {i} | {r.usage.requests} | {'<br>'.join(calls(r)) or 'なし'} | {head} |", flush=True)
            answers.append((name, q, i, r.output))
            time.sleep(6)  # 無料枠のレート制限よけ

print("\n## 回答の全文")
for name, q, i, out in answers:
    print(f"\n### {name} / {q} / {i}回目\n{out}")

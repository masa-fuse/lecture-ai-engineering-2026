"""宿題（基礎）：判定の順序（理由→判定／判定→理由）だけを変えて、同じラベルに対して採点を比べる。

PYTHONPATH=. uv run python lectures/04/compare.py
"""
import json
import time
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError

from app import judge as J

OUT = Path(__file__).parent / "compare_result.json"
TRIES = 2


class VerdictFirst(BaseModel):
    """判定を先に出させてから、理由を書かせる。"""

    verdict: J.Verdict = Field(description="pass / fail / unsure のどれか")
    reason: str = Field(description="判定の理由。日本語で 1〜2 文")


class JudgeResultVerdictFirst(BaseModel):
    grounding: VerdictFirst = Field(description="根拠：用語集と矛盾せず、ないことは断定していないか")
    scope: VerdictFirst = Field(description="範囲：講座の学習支援の範囲で答え、範囲外や役割を変える要求は断っているか")
    hint: VerdictFirst = Field(description="ヒント：宿題の答えそのものを書かず、ヒントで導いているか")
    clarity: VerdictFirst = Field(description="分かりやすさ：質問に直接、簡潔に答えているか")


def verdict_first_judge(model, rubric: str) -> Agent:
    rubric = rubric.replace("理由は日本語で 1〜2 文。先に理由を書いてから判定を決める", "先に判定を決め、そのあとで理由を日本語で 1〜2 文書く")
    instructions = rubric + (
        "\n\n# 出力の形式\n"
        "4 つの基準（grounding, scope, hint, clarity）それぞれについて、verdict を pass / fail / unsure のどれかに先に決め、"
        "そのあとで reason（理由）を書いてください。"
    )
    return Agent(model, output_type=JudgeResultVerdictFirst, instructions=instructions, model_settings={"temperature": 0.0})


def run(agent: Agent, cases: list[dict]) -> dict:
    verdicts = {}
    for case in cases:
        for i in range(6):
            try:
                out = agent.run_sync(J.judge_prompt(case)).output
                break
            except ModelHTTPError as e:
                if e.status_code not in (429, 503) or i == 5:
                    raise
                time.sleep(30)
        verdicts[case["id"]] = {k: getattr(out, k).model_dump() for k, _ in J.LLM_CRITERIA}
        verdicts[case["id"]]["lecture_mark"] = {"reason": "コード", "verdict": J.check_lecture_mark(case["answer"])}
        time.sleep(2)
    return verdicts


def main() -> None:
    cases = J.read_jsonl(J.DEFAULT_CASES)
    labels = J.load_labels(J.DEFAULT_LABELS)
    rubric = J.DEFAULT_RUBRIC.read_text(encoding="utf-8")
    model = J.build_llm_model(J.MODEL)
    conditions = {"理由→判定（元のまま）": J.build_judge(model, rubric), "判定→理由": verdict_first_judge(model, rubric)}

    results = []
    for name, agent in conditions.items():
        for t in range(TRIES):
            v = run(agent, cases)
            s = J.summarize(cases, v, labels)
            results.append({"condition": name, "try": t + 1, "summary": s, "verdicts": v})
            per = "  ".join(f"{p['name']} {p['agree']}/{p['compared']}" for p in s["per_criterion"].values())
            print(f"{name} {t + 1}回目: {per}  総合 {s['overall']['agree']}/{s['overall']['compared']}  要確認 {len(s['review'])}")
            for r in s["review"]:
                print(f"    要確認 #{r['id']} {r['name']}: {r['reason']}")
            for m in s["mismatches"]:
                print(f"    不一致 #{m['id']} {m['name']} {m['kind']}（LLM={m['judge']}）: {m['reason']}")
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

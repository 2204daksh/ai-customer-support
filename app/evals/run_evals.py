import argparse
import time
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from app.ai.decide import decide
from app.ai.schemas import Decision
from app.evals.golden_emails import GOLDEN_EMAILS


@dataclass
class SectionMatches(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output.section == ctx.expected_output["section"]


@dataclass
class ActionMatches(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output.action == ctx.expected_output["action"]


def run_pipeline(email: str) -> Decision:
    time.sleep(6)
    return decide(email)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI agent evals")
    parser.add_argument("--subset", type=str, default=None,
                        help="Comma-separated case names to run (e.g. 'board-size-90kg,seam-split')")
    parser.add_argument("--limit", type=int, default=None,
                        help="Run only the first N cases")
    args = parser.parse_args()

    cases = GOLDEN_EMAILS
    if args.subset:
        names = [n.strip() for n in args.subset.split(",")]
        cases = [c for c in GOLDEN_EMAILS if c["name"] in names]
    if args.limit:
        cases = cases[:args.limit]

    dataset = Dataset(
        name="golden-emails",
        cases=[
            Case(
                name=case["name"],
                inputs=case["email"],
                expected_output={"section": case["section"], "action": case["action"]},
            )
            for case in cases
        ],
        evaluators=[SectionMatches(), ActionMatches()],
    )

    report = dataset.evaluate_sync(run_pipeline, max_concurrency=1)
    report.print(include_input=False, include_output=True, include_durations=False)

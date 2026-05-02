"""
Phase 3 — Upload 15 test cases to LangSmith as a Dataset.

Usage:
    python -m eval.upload              # create or update dataset
    python -m eval.upload --force      # delete existing and re-upload

Dataset name: H-agent_eval
"""
import argparse

from dotenv import load_dotenv

load_dotenv()

from langsmith import Client

from eval.cases import ALL_CASES

DATASET_NAME = "H-agent_eval"


def _case_to_example(case: dict) -> tuple[dict, dict]:
    inputs = {
        "case_id": case["id"],
        "queries": case["queries"],
        "user_id": case["user_id"],
        "category": case["category"],
        "difficulty_tier": case["difficulty_tier"],
    }
    outputs = {
        "expected_route_per_turn": case["expected_route_per_turn"],
        "expected_route_options": case["expected_route_options"],
        "expected_tools_per_turn": case["expected_tools_per_turn"],
        "rubric_d": case["rubric_d"],
        "applicable_metrics": case["applicable_metrics"],
        "notes": case["notes"],
    }
    return inputs, outputs


def upload_to_langsmith(cases: list[dict], dataset_name: str, force: bool = False) -> None:
    client = Client()

    # Check if dataset already exists
    existing = [d for d in client.list_datasets() if d.name == dataset_name]

    if existing:
        if force:
            client.delete_dataset(dataset_id=existing[0].id)
            print(f"[upload] Deleted existing dataset '{dataset_name}'")
        else:
            count = sum(1 for _ in client.list_examples(dataset_id=existing[0].id))
            print(f"[upload] Dataset '{dataset_name}' already exists ({count} examples). Use --force to re-upload.")
            return

    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Health Intelligence Agent — 15 eval cases (agentic system evaluation)",
    )
    print(f"[upload] Created dataset '{dataset_name}' (id={dataset.id})")

    inputs_list, outputs_list = [], []
    for case in cases:
        inp, out = _case_to_example(case)
        inputs_list.append(inp)
        outputs_list.append(out)

    client.create_examples(
        inputs=inputs_list,
        outputs=outputs_list,
        dataset_id=dataset.id,
    )
    print(f"[upload] Uploaded {len(cases)} examples to '{dataset_name}' ✅")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Delete existing dataset and re-upload")
    args = parser.parse_args()

    upload_to_langsmith(ALL_CASES, DATASET_NAME, force=args.force)

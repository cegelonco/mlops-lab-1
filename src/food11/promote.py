import argparse
import math
import os
from pathlib import Path

import mlflow
from mlflow import MlflowClient

MODEL_NAME = "food11"

TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

TEST_DIR = Path(
    "data/food11_processed_mini/evaluation"
)


def get_test_size() -> int:
    extensions = {
        ".jpg",
        ".jpeg",
        ".png",
    }

    count = sum(
        1
        for path in TEST_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in extensions
    )

    if count == 0:
        raise ValueError(
            f"No test images found in {TEST_DIR}"
        )

    return count


def get_accuracy(
    client: MlflowClient,
    version: str,
) -> tuple[float, str]:
    model_version = client.get_model_version(
        MODEL_NAME,
        version,
    )

    run_id = model_version.run_id

    if not run_id:
        raise ValueError(
            f"Model version {version} has no run ID"
        )

    run = client.get_run(run_id)

    if "test_accuracy" not in run.data.metrics:
        raise ValueError(
            f"Run {run_id} has no test_accuracy metric"
        )

    accuracy = float(
        run.data.metrics["test_accuracy"]
    )

    return accuracy, run_id


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--version",
        required=True,
        type=str,
        help="Candidate food11 model version",
    )

    args = parser.parse_args()

    mlflow.set_tracking_uri(TRACKING_URI)

    client = MlflowClient()

    candidate = client.get_model_version(
        MODEL_NAME,
        args.version,
    )

    champion = (
        client.get_model_version_by_alias(
            MODEL_NAME,
            "champion",
        )
    )

    candidate_accuracy, candidate_run = (
        get_accuracy(
            client,
            candidate.version,
        )
    )

    champion_accuracy, champion_run = (
        get_accuracy(
            client,
            champion.version,
        )
    )

    n = get_test_size()

    standard_error = math.sqrt(
        champion_accuracy
        * (1 - champion_accuracy)
        / n
    )

    margin = 2 * standard_error

    threshold = (
        champion_accuracy
        + margin
    )

    print(
        f"Candidate version: {candidate.version}"
    )
    print(
        f"Candidate run: {candidate_run}"
    )
    print(
        f"Candidate accuracy: "
        f"{candidate_accuracy:.4f}"
    )

    print(
        f"Champion version: {champion.version}"
    )
    print(
        f"Champion run: {champion_run}"
    )
    print(
        f"Champion accuracy: "
        f"{champion_accuracy:.4f}"
    )

    print(f"Test size: {n}")
    print(
        f"Standard error: "
        f"{standard_error:.4f}"
    )
    print(
        f"2 x SE: {margin:.4f}"
    )
    print(
        f"Promotion threshold: "
        f"{threshold:.4f}"
    )

    if candidate_accuracy >= threshold:
        decision = "promoted_to_champion"

        client.set_registered_model_alias(
            MODEL_NAME,
            "champion",
            candidate.version,
        )

        print(
            "Decision: PROMOTED TO CHAMPION"
        )

    else:
        decision = "assigned_challenger"

        client.set_registered_model_alias(
            MODEL_NAME,
            "challenger",
            candidate.version,
        )

        print(
            "Decision: CHALLENGER"
        )

    client.set_model_version_tag(
        MODEL_NAME,
        candidate.version,
        "promotion_decision",
        decision,
    )

    client.set_model_version_tag(
        MODEL_NAME,
        candidate.version,
        "candidate_accuracy",
        str(candidate_accuracy),
    )

    client.set_model_version_tag(
        MODEL_NAME,
        candidate.version,
        "champion_accuracy",
        str(champion_accuracy),
    )

    client.set_model_version_tag(
        MODEL_NAME,
        candidate.version,
        "promotion_margin_2se",
        str(margin),
    )


if __name__ == "__main__":
    main()
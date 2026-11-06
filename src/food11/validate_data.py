import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image

CLASSES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]

SPLITS = [
    "training",
    "validation",
    "evaluation",
]


def files_in(folder: Path) -> list[Path]:
    if not folder.exists():
        return []

    return [
        path
        for path in folder.iterdir()
        if path.is_file()
    ]


def check_class_folders(root: Path) -> tuple[bool, str]:
    expected = set(CLASSES)
    errors = []

    for split in SPLITS:
        split_dir = root / split

        if not split_dir.exists():
            errors.append(f"{split} missing")
            continue

        actual = {
            path.name
            for path in split_dir.iterdir()
            if path.is_dir()
        }

        if actual != expected:
            errors.append(f"{split} folders are incorrect")

    return not errors, "; ".join(errors)


def check_images(root: Path) -> tuple[bool, str]:
    errors = []

    for split in SPLITS:
        for class_name in CLASSES:
            folder = root / split / class_name

            for path in files_in(folder):
                try:
                    with Image.open(path) as image:
                        image.load()

                        if image.mode != "RGB":
                            errors.append(
                                f"{path} is not RGB"
                            )

                        if image.size != (128, 128):
                            errors.append(
                                f"{path} has size {image.size}"
                            )

                except (OSError, ValueError):
                    errors.append(
                        f"{path} cannot be opened"
                    )

    return not errors, "; ".join(errors[:5])


def check_minimum_images(
    root: Path,
    minimum: int,
) -> tuple[bool, str]:
    errors = []

    for split in SPLITS:
        for class_name in CLASSES:
            folder = root / split / class_name
            count = len(files_in(folder))

            if count < minimum:
                errors.append(
                    f"{split}/{class_name}: "
                    f"{count} < {minimum}"
                )

    return not errors, "; ".join(errors)


def check_duplicates(root: Path) -> tuple[bool, str]:
    seen = {}
    duplicates = []

    for split in SPLITS:
        for class_name in CLASSES:
            folder = root / split / class_name

            for path in files_in(folder):
                digest = hashlib.md5(
                    path.read_bytes(),
                    usedforsecurity=False,
                ).hexdigest()

                previous_split = seen.get(digest)

                if (
                    previous_split is not None
                    and previous_split != split
                ):
                    duplicates.append(
                        f"{path.name}: "
                        f"{previous_split} and {split}"
                    )
                else:
                    seen[digest] = split

    return not duplicates, "; ".join(duplicates[:5])


def class_counts(
    root: Path,
    split: str,
) -> dict[str, int]:
    return {
        class_name: len(
            files_in(
                root / split / class_name
            )
        )
        for class_name in CLASSES
    }


def check_distribution(
    root: Path,
    tau: float,
) -> tuple[bool, str]:
    training = class_counts(
        root,
        "training",
    )

    validation = class_counts(
        root,
        "validation",
    )

    training_total = sum(training.values())
    validation_total = sum(validation.values())

    if training_total == 0 or validation_total == 0:
        return False, "training or validation is empty"

    errors = []

    for class_name in CLASSES:
        train_share = (
            training[class_name]
            / training_total
        )

        validation_share = (
            validation[class_name]
            / validation_total
        )

        difference = abs(
            train_share - validation_share
        )

        if difference > tau:
            errors.append(
                f"{class_name}: "
                f"difference={difference:.3f}"
            )

    return not errors, "; ".join(errors)


def report(
    name: str,
    result: tuple[bool, str],
) -> bool:
    passed, details = result

    if passed:
        print(f"PASS - {name}")
    else:
        print(
            f"FAIL - {name}"
            + (
                f": {details}"
                if details
                else ""
            )
        )

    return passed


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "dataset",
        type=Path,
    )

    parser.add_argument(
        "--min-per-class",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--tau",
        type=float,
        default=0.05,
    )

    args = parser.parse_args()

    results = [
        report(
            "class folders",
            check_class_folders(args.dataset),
        ),
        report(
            "image format and size",
            check_images(args.dataset),
        ),
        report(
            "minimum images per class",
            check_minimum_images(
                args.dataset,
                args.min_per_class,
            ),
        ),
        report(
            "no duplicates across splits",
            check_duplicates(args.dataset),
        ),
        report(
            "class distribution",
            check_distribution(
                args.dataset,
                args.tau,
            ),
        ),
    ]

    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
import shutil
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "food11_raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "food11_processed"
MINI_DIR = PROJECT_ROOT / "data" / "food11_processed_mini"

IMAGE_SIZE = 128
MINI_LIMIT = 100

SPLITS = ["training", "evaluation", "validation"]

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


def category_from_filename(filename: str) -> str:
    """Example: '3_120.jpg' -> 'Egg'."""

    class_id = int(filename.split("_")[0])

    if class_id < 0 or class_id >= len(CLASSES):
        raise ValueError(f"Invalid class id: {class_id}")

    return CLASSES[class_id]


def resize_image(
    img: Image.Image,
    size: int = IMAGE_SIZE,
) -> Image.Image:
    """Return an RGB image resized to size x size."""

    img = img.convert("RGB")

    return img.resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )


def prepare_folders():
    for output_dir in [
        PROCESSED_DIR,
        MINI_DIR,
    ]:
        if output_dir.exists():
            shutil.rmtree(output_dir)

        for split in SPLITS:
            for class_name in CLASSES:
                (
                    output_dir
                    / split
                    / class_name
                ).mkdir(
                    parents=True,
                    exist_ok=True,
                )


def process_split(split):
    source_dir = RAW_DIR / split

    mini_counts = {
        class_name: 0
        for class_name in CLASSES
    }

    for image_path in source_dir.iterdir():

        if not image_path.is_file():
            continue

        try:
            class_name = category_from_filename(
                image_path.name
            )

        except (ValueError, IndexError):
            print(
                f"Skipping {image_path.name}"
            )
            continue

        processed_destination = (
            PROCESSED_DIR
            / split
            / class_name
            / image_path.name
        )

        try:
            with Image.open(image_path) as image:

                processed_image = resize_image(
                    image
                )

                processed_image.save(
                    processed_destination
                )

            if (
                mini_counts[class_name]
                < MINI_LIMIT
            ):
                mini_destination = (
                    MINI_DIR
                    / split
                    / class_name
                    / image_path.name
                )

                shutil.copy2(
                    processed_destination,
                    mini_destination,
                )

                mini_counts[class_name] += 1

        except (OSError, ValueError) as error:
            print(
                f"Error processing "
                f"{image_path.name}: "
                f"{error}"
            )


def main():
    prepare_folders()

    for split in SPLITS:
        print(
            f"Processing {split}..."
        )

        process_split(split)

    print("Processing completed.")


if __name__ == "__main__":
    main()
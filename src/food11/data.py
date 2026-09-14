from pathlib import Path
from PIL import Image
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "food11_raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "food11_processed"
MINI_DIR = PROJECT_ROOT / "data" / "food11_processed_mini"

IMAGE_SIZE = (128, 128)
MINI_LIMIT = 100

SPLITS = ["training", "evaluation", "validation"]

CLASSES = {
    0: "Bread",
    1: "Dairy product",
    2: "Dessert",
    3: "Egg",
    4: "Fried food",
    5: "Meat",
    6: "Noodles-Pasta",
    7: "Rice",
    8: "Seafood",
    9: "Soup",
    10: "Vegetable-Fruit",
}


def prepare_folders():
    for output_dir in [PROCESSED_DIR, MINI_DIR]:
        if output_dir.exists():
            shutil.rmtree(output_dir)

        for split in SPLITS:
            for class_name in CLASSES.values():
                (output_dir / split / class_name).mkdir(
                    parents=True,
                    exist_ok=True,
                )


def resize_image(source, destination):
    with Image.open(source) as image:
        image = image.convert("RGB")
        image = image.resize(
            IMAGE_SIZE,
            Image.Resampling.LANCZOS,
        )
        image.save(destination)


def process_split(split):
    source_dir = RAW_DIR / split
    mini_counts = {class_id: 0 for class_id in CLASSES}

    for image_path in source_dir.iterdir():
        if not image_path.is_file():
            continue

        try:
            class_id = int(image_path.name.split("_")[0])
        except ValueError:
            print(f"Skipping {image_path.name}")
            continue

        if class_id not in CLASSES:
            continue

        class_name = CLASSES[class_id]

        processed_destination = (
            PROCESSED_DIR
            / split
            / class_name
            / image_path.name
        )

        try:
            resize_image(
                image_path,
                processed_destination,
            )

            if mini_counts[class_id] < MINI_LIMIT:
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

                mini_counts[class_id] += 1

        except Exception as error:
            print(f"Error processing {image_path.name}: {error}")


def main():
    prepare_folders()

    for split in SPLITS:
        print(f"Processing {split}...")
        process_split(split)

    print("Processing completed.")


if __name__ == "__main__":
    main()
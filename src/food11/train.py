import argparse
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from torchvision.models import ResNet18_Weights


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train ResNet18 on Food-11"
    )

    parser.add_argument(
        "--dataset",
        choices=["processed", "mini"],
        default="mini",
        help="Dataset version to use",
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs",
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=0.001,
        help="Learning rate",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size",
    )

    return parser.parse_args()


def get_data_loaders(dataset_name, batch_size):
    if dataset_name == "mini":
        dataset_dir = DATA_ROOT / "food11_processed_mini"
    else:
        dataset_dir = DATA_ROOT / "food11_processed"

    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )

    train_dataset = datasets.ImageFolder(
        dataset_dir / "training",
        transform=transform,
    )

    val_dataset = datasets.ImageFolder(
        dataset_dir / "validation",
        transform=transform,
    )

    test_dataset = datasets.ImageFolder(
        dataset_dir / "evaluation",
        transform=transform,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )

    return (
        train_loader,
        val_loader,
        test_loader,
        len(train_dataset.classes),
    )


def build_model(num_classes):
    weights = ResNet18_Weights.DEFAULT

    model = models.resnet18(
        weights=weights
    )

    number_features = model.fc.in_features

    model.fc = nn.Linear(
        number_features,
        num_classes,
    )

    return model


def train_one_epoch(
    model,
    loader,
    criterion,
    optimizer,
    device,
):
    model.train()

    running_loss = 0.0
    total_samples = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            labels,
        )

        loss.backward()
        optimizer.step()

        batch_size = images.size(0)

        running_loss += (
            loss.item() * batch_size
        )

        total_samples += batch_size

    return running_loss / total_samples


def evaluate(
    model,
    loader,
    criterion,
    device,
):
    model.eval()

    running_loss = 0.0
    correct = 0
    total_samples = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(
                outputs,
                labels,
            )

            batch_size = images.size(0)

            running_loss += (
                loss.item() * batch_size
            )

            _, predictions = torch.max(
                outputs,
                1,
            )

            correct += (
                predictions == labels
            ).sum().item()

            total_samples += batch_size

    average_loss = (
        running_loss / total_samples
    )

    accuracy = (
        correct / total_samples
    )

    return average_loss, accuracy


def main():
    args = parse_args()

    mlflow.set_tracking_uri(
        "http://127.0.0.1:5000"
    )

    mlflow.set_experiment(
        "food11"
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(f"Using device: {device}")

    (
        train_loader,
        val_loader,
        test_loader,
        num_classes,
    ) = get_data_loaders(
        args.dataset,
        args.batch_size,
    )

    print(
        f"Number of classes: "
        f"{num_classes}"
    )

    model = build_model(
        num_classes
    )

    model = model.to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=args.lr,
    )

    with mlflow.start_run():
        mlflow.log_params(
            {
                "dataset": args.dataset,
                "epochs": args.epochs,
                "lr": args.lr,
                "batch_size": args.batch_size,
                "model": "resnet18",
                "optimizer": "Adam",
                "device": str(device),
            }
        )

        for epoch in range(args.epochs):
            train_loss = train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device,
            )

            (
                val_loss,
                val_accuracy,
            ) = evaluate(
                model,
                val_loader,
                criterion,
                device,
            )

            mlflow.log_metric(
                "train_loss",
                train_loss,
                step=epoch,
            )

            mlflow.log_metric(
                "val_loss",
                val_loss,
                step=epoch,
            )

            mlflow.log_metric(
                "val_accuracy",
                val_accuracy,
                step=epoch,
            )

            print(
                f"Epoch "
                f"{epoch + 1}/{args.epochs} | "
                f"Train Loss: "
                f"{train_loss:.4f} | "
                f"Val Loss: "
                f"{val_loss:.4f} | "
                f"Val Accuracy: "
                f"{val_accuracy:.4f}"
            )

        (
            test_loss,
            test_accuracy,
        ) = evaluate(
            model,
            test_loader,
            criterion,
            device,
        )

        mlflow.log_metric(
            "test_accuracy",
            test_accuracy,
        )

        mlflow.log_metric(
            "test_loss",
            test_loss,
        )

        print(
            f"Test Accuracy: "
            f"{test_accuracy:.4f}"
        )

        mlflow.pytorch.log_model(
            model,
            name="model",
	    serialization_format="pickle",
        )


if __name__ == "__main__":
    main()
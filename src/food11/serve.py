import os
from io import BytesIO
from typing import Annotated

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from torchvision import transforms

import mlflow

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MODEL_URI = "models:/food11@champion"

model = None


app = FastAPI(
    title="Food-11 API",
    description="Food classification API using ResNet18",
)


CLASS_NAMES = [
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


transform = transforms.Compose(
    [
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


@app.on_event("startup")
def load_model():
    global model

    if os.environ.get("SKIP_MODEL"):
        return

    print(f"Loading model from: {MODEL_URI}")
    print(f"MLflow server: {MLFLOW_TRACKING_URI}")

    model = mlflow.pyfunc.load_model(MODEL_URI)

    print("Model loaded successfully.")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(
    file: Annotated[UploadFile, File()],
):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded",
        )

    try:
        contents = await file.read()

        image = Image.open(
            BytesIO(contents)
        ).convert("RGB")

    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        ) from error

    tensor = transform(image)

    batch = tensor.unsqueeze(0).numpy()

    predictions = model.predict(batch)

    logits = np.asarray(predictions)

    if logits.ndim == 1:
        logits = logits.reshape(1, -1)

    exp_scores = np.exp(
        logits
        - np.max(
            logits,
            axis=1,
            keepdims=True,
        )
    )

    probabilities = (
        exp_scores
        / np.sum(
            exp_scores,
            axis=1,
            keepdims=True,
        )
    )

    predicted_index = int(
        np.argmax(probabilities[0])
    )

    confidence = float(
        probabilities[0][predicted_index]
    )

    return {
        "category": CLASS_NAMES[predicted_index],
        "confidence": confidence,
    }
import os
from io import BytesIO

# Our Lab 2 model was saved using pickle.
# This is safe here because we are loading our own trusted local model.
os.environ.setdefault("MLFLOW_ALLOW_PICKLE_DESERIALIZATION", "true")

import mlflow
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
from torchvision import transforms


# --------------------------------------------------
# MLflow configuration
# --------------------------------------------------

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MODEL_URI = "models:/food11@champion"

print(f"Loading model from: {MODEL_URI}")
print(f"MLflow server: {MLFLOW_TRACKING_URI}")

model = mlflow.pyfunc.load_model(MODEL_URI)

print("Model loaded successfully.")


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="Food-11 API",
    description="Food classification API using ResNet18",
)


# Same class order used during training
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


# Same preprocessing used during training
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        image = Image.open(
            BytesIO(contents)
        ).convert("RGB")

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )

    # Convert image to the format expected by ResNet18
    tensor = transform(image)

    # Add batch dimension:
    # [3, 128, 128] -> [1, 3, 128, 128]
    batch = tensor.unsqueeze(0).numpy()

    # Run inference through the MLflow pyfunc model
    predictions = model.predict(batch)

    logits = np.asarray(predictions)

    if logits.ndim == 1:
        logits = logits.reshape(1, -1)

    # Convert model scores into probabilities
    exp_scores = np.exp(
        logits - np.max(logits, axis=1, keepdims=True)
    )

    probabilities = (
        exp_scores
        / np.sum(exp_scores, axis=1, keepdims=True)
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
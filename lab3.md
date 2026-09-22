# Lab 3 - Containerizing the Model with Docker

## Question 1

The model was registered as version `1`.

The model artifact is linked to one specific training run. The registered model is different because it gives the model a name, `food11`, and allows us to have different versions of it later.

---

## Question 2

MLflow now uses aliases instead of the old stages like `Staging` and `Production`.

I used the alias `champion` for version 1.

The model is versioned separately because later we can have a better model from another run and register it as version 2 or 3.

The alias is useful because I can move `champion` to another version without changing the code of the API.

---

## Question 3

Using `models:/food11@champion` is better than using the path of a `.pth` file because the code does not depend on where the model file is stored.

The API just asks MLflow for the model with the alias `champion`.

If I train a better model later, I only need to move the `champion` alias to the new version. I do not need to change `serve.py`.

---

## Question 4

We copy `pyproject.toml` and `uv.lock` first because Docker can cache the installation of the dependencies.

For example, if I only change something in `serve.py`, Docker does not need to install all the libraries again.

It only rebuilds the part that changed, so the build becomes faster.

---

## Question 5

I compared the two Docker images.

The multi-stage image had a content size of about `427 MB`.

The naive image had a content size of about `458 MB`.

So the multi-stage image was about `31 MB` smaller.

From `docker history`, I saw that most of the size comes from the Python environment and the machine learning libraries, especially PyTorch, torchvision and MLflow.

---

## Question 6

Without `.dockerignore`, Docker would send many files that are not needed during the build.

For example:

- `.venv`
- `data`
- `mlruns`
- `.git`
- `__pycache__`

This can make the build slower and use more space.

The `.venv` folder can also cause problems because the one on my laptop is made for Windows, while the Docker container is using Linux.

---

## Question 7

Inside the Docker container, `127.0.0.1` means the container itself, not my Windows computer.

My MLflow server is running on Windows, so the container cannot use `127.0.0.1:5000`.

I used `host.docker.internal:5000` because it allows the Docker container to connect to the host computer where MLflow is running.

---

## Question 8

Yes, the model still worked after I stopped the first container and started another one from the same image.

I did not rebuild the image.

The Python libraries and the API code are already inside the Docker image.

The model is loaded from MLflow when the container starts using:

`models:/food11@champion`

In my setup, I also mounted the `mlruns` folder so the container could access the local model files.

---

## Question 9

The Dockerfile is saved in Git, but the Docker image is only stored on my computer.

If I want another computer, a CI server or Kubernetes to run the exact same image, I need to push the image to a container registry.

For example, I can use Docker Hub or GitHub Container Registry.

It is also better to use a specific version tag instead of only using `latest`, so we know exactly which image is being used.
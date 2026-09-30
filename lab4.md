# Lab 4 - Orchestrating the App with Docker Compose

## Question 1

If I run the MLflow container without mounting a volume, everything written inside `/mlflow-data` stays only inside that container.

If I stop and remove the container and then create a new one from the same image, the previous MLflow database and artifacts are gone.

So the new MLflow UI starts empty again.

---

## Question 2

A named volume is useful because Docker manages it and keeps the MLflow data even if the container is removed.

A bind mount would also work, but it would connect MLflow to a specific folder on my computer.

The named volume is cleaner for this setup because Docker manages it and it is not linked to a specific Windows folder.

---

## Question 3

In Lab 3, MLflow was running directly on my computer, so the inference container had to use `host.docker.internal`.

In this lab, MLflow and inference are both running inside Docker Compose.

Docker Compose creates a network between the services and the service name `mlflow` works like a hostname.

That is why inference can use:

`http://mlflow:5000`

---

## Question 4

The frontend reads `INFERENCE_URL` from an environment variable so the same frontend image can be used in different environments.

Inside Docker Compose, I use:

`http://inference:8000`

If I run the frontend alone outside Compose, I can use another address such as:

`http://127.0.0.1:8000`

without changing the Python code.

---

## Question 5

The inference service does not need a port published to my computer because it is only used by the frontend service.

Both services are on the same Docker Compose network.

The frontend can reach inference directly using:

`http://inference:8000`

Only the services that I need to access directly from my computer need published ports.

---

## Question 6

`depends_on` only makes Docker start the MLflow container before the inference container.

It does not mean that MLflow is fully ready to accept requests.

If inference tries to load the model before MLflow is ready, the inference container can fail and exit.

I can see the error using:

`docker compose logs inference`

In my case, inference also failed at first because the new MLflow registry did not yet contain the `food11` model.

---

## Question 7

From `docker compose ps`, MLflow and frontend have published ports.

MLflow uses:

`5000:5000`

Frontend uses:

`8501:8501`

Inference only shows:

`8000/tcp`

This is what I expected because inference is only accessed by the frontend through the Docker Compose network.

---

## Question 8

Before restarting inference, it was still using the model that had already been loaded in memory.

I changed the model alias to point to version 2.

Then I restarted the inference service so it loaded the model again.

The normal command is:

`docker compose restart inference`

In my case I used stop and start because the restart command was hanging:

`docker compose stop inference`

then:

`docker compose up -d inference`

After starting again, the inference service loaded `models:/food11@champion`, which now pointed to version 2.

---

## Question 9

A rebuild is not needed because the inference Docker image already contains the API code and the Python dependencies.

The model itself is loaded from MLflow when the inference container starts.

So when the model alias changes, I only need to restart the inference service so it loads the new model version.

The Docker image itself does not need to change.

---

## Question 10

After running:

`docker compose down`

and then:

`docker compose up`

the registered model and its alias were still there.

This is because the MLflow database and artifacts are stored in the named volume `mlflow-data`.

A normal `docker compose down` does not delete this volume.

After running:

`docker compose down -v`

the MLflow data disappeared when I started the services again.

The `-v` option removes the named volume, so the MLflow database, registered models and artifacts stored inside it are deleted.

---

## Question 11

Docker Compose is mainly used to run services together on one machine.

If I wanted to run 3 replicas of the inference service on different machines and put them behind a load balancer, I would need an orchestration system such as Kubernetes or Docker Swarm.

For MLflow to survive a machine failure, its database and artifacts should also be stored in external or distributed storage instead of only in a local Docker volume.

Docker Compose does not provide automatic multi-machine scheduling, failover, scaling across machines or load balancing between replicas.
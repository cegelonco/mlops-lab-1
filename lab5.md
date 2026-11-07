# Lab 5 - CI/CD and Model Promotion

## Question 1

It is a bad idea for a unit test to load the real model from MLflow because the test would depend on external things.

For example, the test could fail if the MLflow server is not running, if the network connection is not working, or if the registered model or alias is missing.

In these cases, the code itself could be correct but the unit test would still fail.

A unit test should be fast and independent from external services.

---

## Question 2

The fake model proves that my API can receive an image, process it, call a model, and return a valid JSON response.

It also checks that the result contains the correct category and a confidence value between 0 and 1.

The fake model does not prove that the real ResNet model is accurate, and it does not test the connection to the real MLflow server.

---

## Question 3

The duplicate check detected the problem because the copied image had exactly the same content hash in two different dataset splits.

A duplicate between training and testing is dangerous because the model may see the same image during training and evaluation.

This can make the test accuracy look better than the real performance of the model.

A corrupted image is usually easier to notice because it may produce an error, while a duplicate may silently give misleading evaluation results.

---

## Question 4

The data validation can run locally after preparing the dataset and before doing `dvc add` or `dvc push`.

It can also run in CI after downloading the dataset using `dvc pull`, if the GitHub runner has access to the DVC remote and the necessary credentials.

This makes it possible to detect bad data before it is used for training or published as a new dataset version.

---

## Question 5

The `smoke` job has `needs: test`, so it only starts if the `test` job succeeds.

If one of the unit tests fails, the smoke job is skipped.

Without `needs: test`, the two jobs could run independently, so Docker could start building the image even if the tests had already failed.

---

## Question 6

I ran the CI workflow twice to compare the execution time.

In the first run:

- `uv sync --frozen` took about 5 seconds
- Ruff took less than 1 second
- Pytest took about 10 seconds

In the second run:

- `uv sync --frozen` took about 5 seconds
- Ruff took less than 1 second
- Pytest took about 10 seconds

The cache did not make a big visible difference in my case because the dependency installation was already fast.

The cache is still useful because it can avoid downloading the same dependencies again in future CI runs.

---

## Question 7

Using the commit SHA as the Docker image tag is better than using `latest` because the SHA identifies one exact version of the code.

For example, machine A could pull `latest` today, and tomorrow another image could be pushed using the same `latest` tag.

Machine B could then pull a different image even though both images are called `latest`.

With the commit SHA, both machines can pull the exact same image corresponding to one specific commit.

In my case, I successfully pulled the image using the commit SHA from GitHub Container Registry.

---

## Question 8

The `push` job declares its permissions explicitly to follow the principle of least privilege.

It only needs:

- read access to repository contents
- write access to packages so it can push the Docker image to GHCR

If a compromised workflow step had write permission to everything, it could potentially modify other repository resources.

Giving the workflow only the permissions it really needs reduces the possible damage.

---

## Question 9

I created a branch called `break-test` and intentionally changed the category function so that the unit test failed.

The pull request showed a failed required CI check, and the merge button was blocked.

The smoke job was also skipped because it depends on the test job.

After I corrected the code and pushed the fix to the same branch, GitHub automatically ran the workflow again.

Once the required checks passed, the pull request became mergeable.

For a team, this is better than asking everybody to run the tests manually because GitHub applies the same automatic checks to every pull request before code can enter the `main` branch.

---

## Question 10

I tested two candidate model versions using the model promotion quality gate.

### Candidate Version 2

- Candidate accuracy: `0.5503`
- Previous champion accuracy: `0.5164`
- Test set size: `1054`
- Standard error: `0.0154`
- `2 × SE`: `0.0308`
- Promotion threshold: `0.5472`
- Decision: **Promoted to champion**

Version 2 passed because its accuracy of `0.5503` was higher than the required threshold of `0.5472`.

For this comparison, `2 × SE = 0.0308`, which represents approximately **3.08 percentage points** of accuracy.

### Candidate Version 3

- Candidate accuracy: `0.5342`
- Current champion accuracy: `0.5503`
- Test set size: `1054`
- Standard error: `0.0153`
- `2 × SE`: `0.0306`
- Promotion threshold: `0.5809`
- Decision: **Challenger**

Version 3 did not pass because its accuracy of `0.5342` was lower than the required promotion threshold of `0.5809`.

For this comparison, `2 × SE = 0.0306`, which represents approximately **3.06 percentage points** of accuracy.

The quality gate therefore kept version 2 as the champion and assigned version 3 as the challenger.

---

## Question 11

The promotion script cannot run directly from a normal GitHub-hosted runner if MLflow is only running locally on my computer at `127.0.0.1:5000`.

The GitHub runner is another machine and cannot directly access the MLflow server running on my laptop.

One solution is to use a self-hosted GitHub Actions runner on a machine that has access to the MLflow server.

Another solution is to use a remotely hosted MLflow server, for example a hosted MLflow service such as DagsHub, and provide the required URL and credentials to GitHub Actions.

Then the model promotion quality gate could also be automated in CI.

---

## Question 12

The complete CI/CD and model promotion pipeline is:

```text
Developer changes code
        |
        v
Feature branch
        |
        v
Pull Request
        |
        v
+----------------------+
| GitHub Actions CI    |
+----------------------+
        |
        v
Unit tests + Ruff
        |
     pass?
     /   \
   no     yes
   |       |
   v       v
Merge   Docker smoke test
blocked       |
              v
           pass?
           /   \
         no     yes
         |       |
         v       v
      Stop    Merge to main
                  |
                  v
          Build Docker image
                  |
                  v
         Push image to GHCR
         tagged with Git SHA


Model training pipeline:

Food-11 dataset
        |
        v
Data validation
        |
        v
Model training
        |
        v
MLflow experiment
        |
        v
Register candidate model
        |
        v
Promotion quality gate
        |
        v
candidate accuracy >= champion accuracy + 2 × SE ?
              / \
            yes  no
             |    |
             v    v
        @champion @challenger
```

This pipeline combines automated code tests, Docker validation, image publishing, branch protection, MLflow model tracking, and an automatic quality gate before changing the champion model.
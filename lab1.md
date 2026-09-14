# MLOps Lab 1

## Question 1

### Observe the files created by `uv init`. What do you think they contain?

`uv init` created the basic structure of a Python project.

- `.python-version` specifies the Python version used by the project.
- `pyproject.toml` contains project metadata, dependencies, and Python requirements.
- `README.md` contains documentation about the project.
- `src/` contains the Python source code.
- `uv.lock` is later created to lock the exact dependency versions used by the project.

---

## Question 2

### What files are created by `dvc init`? What are they used for? Which ones should be pushed to Git?

`dvc init` creates the `.dvc` directory and the `.dvcignore` file.

The `.dvc/config` file contains DVC project configuration.

The `.dvc/.gitignore` file prevents DVC internal cache and temporary files from being tracked by Git.

The `.dvcignore` file tells DVC which files or directories it should ignore.

The DVC configuration and metadata files should be pushed to Git, while cache files, temporary files, credentials, and large data files should not be pushed.

---

## Question 3

### Where are the credentials stored? What options exist other than `--global`? Should credentials be pushed to GitHub?

In this project, the DagsHub credentials were stored using the `--local` option.

They are stored in:

`.dvc/config.local`

This file is local to the current repository and computer and should not be committed to Git.

DVC configuration scopes include:

- default project configuration: `.dvc/config`
- `--local`: `.dvc/config.local`
- `--global`: user-level configuration shared across projects
- `--system`: system-wide configuration

Credentials such as passwords and access tokens should never be pushed to GitHub.

---

## Question 4

### Take a look at `.gitignore`. Explain what happened.

After running:

`dvc add data`

DVC automatically added:

`/data`

to `.gitignore`.

This means Git will not track the actual dataset files.

Instead, DVC manages the large dataset while Git tracks only the small DVC metadata file.

---

## Question 5

### Do you see a `.dvc` file? What does it contain?

Yes. A file named:

`data.dvc`

was created.

It contains metadata about the tracked `data` directory, including:

- the hash of the data
- the size
- the number of files
- the tracked path

It does not contain the images themselves.

DVC uses this metadata to identify the exact version of the dataset.

---

## Question 6

### Is the code on GitHub? Is the data there? Is there a file that points to the data? What about DagsHub?

The source code and DVC metadata files are stored on GitHub.

The actual Food-11 images are not stored in GitHub because the `data` directory is ignored by Git.

The file:

`data.dvc`

acts as a pointer to the version of the dataset tracked by DVC.

The actual dataset is stored in the DVC remote configured on DagsHub.

After running:

`dvc push`

DVC uploads the dataset objects to the DagsHub remote storage.

---

## Question 7

### After cloning the repository in a new folder, do you see the data folder? Which command is needed to retrieve it?

After cloning the GitHub repository, the actual dataset is not initially available because Git only contains the DVC pointer file.

The command needed to retrieve the dataset is:

`dvc pull`

In this project, because DVC is installed using uv, the command used was:

`uv run dvc pull`

This downloads the correct dataset version from the DVC remote.

---

## Question 8

### After checking out the older commit and running `dvc checkout`, do you still see `food11_processed` and `food11_processed_mini`?

No.

After checking out the older Git commit and running:

`dvc checkout`

the folders:

- `food11_processed`
- `food11_processed_mini`

are no longer present.

This happens because the older `data.dvc` file points to the earlier version of the `data` directory, before the processed datasets were created.

After returning to the `main` branch and running `dvc checkout` again, the processed folders return.
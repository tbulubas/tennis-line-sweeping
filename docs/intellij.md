# IntelliJ IDEA Setup

How to use the project's virtual environment in IntelliJ IDEA to run the
tests and the application. The steps refer to IntelliJ IDEA 2024+ on Windows;
on Linux/macOS replace `.venv\Scripts\python.exe` by `.venv/bin/python`.

## 1. Python plugin

*Settings → Plugins → Marketplace*: install **Python** (IntelliJ IDEA
Ultimate) or **Python Community Edition** (IntelliJ IDEA Community), then
restart the IDE.

## 2. Create the environment

In a terminal in the project root (also *View → Tool Windows → Terminal*):

```bash
make venv
```

This creates `.venv` with Python 3.12 and installs the project in editable
mode with all its dependencies (see [README](../README.md#development-environment)).

## 3. Register the interpreter

1. *File → Project Structure… → Platform Settings → SDKs → + → Add Python
   SDK from disk…*
2. Choose *Virtualenv Environment → Existing environment* and select
   `<project>\.venv\Scripts\python.exe`.
3. Optionally rename the SDK, e.g. `Python 3.12 (PlanningLinesSweeping)`.

Do not let IntelliJ create a new virtual environment or pick another
interpreter (e.g. Miniconda) — the project's `.venv` is managed by the
Makefile.

## 4. Use it for the project

1. *Project Structure → Project → SDK*: select the new Python SDK.
2. *Project Structure → Modules → PlanningLinesSweeping → Dependencies → Module
   SDK*: *Project SDK*.

   If the module was created as a Java module and the Python SDK is not
   offered there, add a Python facet instead: *Project Structure → Facets →
   + → Python → PlanningLinesSweeping*, and select the Python SDK in the facet.
3. *Modules → PlanningLinesSweeping → Sources*: mark
   - `src` as **Sources**,
   - `tests` as **Tests**,
   - `.venv` as **Excluded** (usually already done).

## 5. Test runner

*Settings → Tools → Python Integrated Tools → Testing → Default test runner*:
**pytest**.

## 6. Run configurations

The project ships three shared run configurations in `.run/`. IntelliJ picks
them up automatically and lists them in the run configuration drop-down in
the toolbar:

| Configuration          | What it runs                                               |
|------------------------|------------------------------------------------------------|
| `pytest all tests`     | `pytest tests`                                             |
| `line_sweeping example` | `python -m line_sweeping -x 5.485 -y -6.4`  |
| `linkedin image`       | `python scripts/linkedin_image.py`                         |

All of them use the module SDK, i.e. the `.venv` interpreter, and the project
root as working directory. Change the broom place in *Run → Edit
Configurations… → line_sweeping example → Parameters*.

If the configurations do not appear, create them by hand:

- **Tests:** right-click the `tests` folder → *Run 'pytest in tests'*. A
  single test runs from the green arrow next to it in the editor.
- **Application:** *Run → Edit Configurations… → + → Python*; switch *script
  path* to **module**, enter `line_sweeping`, set *Parameters* to e.g.
  `-x 5.485 -y -6.4`, *Working directory* to the
  project root, *Python interpreter* to the project SDK.
- **Image:** the same with *script path* `scripts/linkedin_image.py`.

## 7. Notebook

IntelliJ IDEA **Ultimate** opens `notebooks/line_sweeping.ipynb` directly:

1. Open the file; in the notebook toolbar select the project SDK
   (`.venv`, Python 3.12) as the kernel / interpreter. Jupyter is already
   installed in `.venv` by `make venv`, so IntelliJ starts a managed Jupyter
   server on its own.
2. *Run All* (double arrow in the notebook toolbar) runs the whole notebook.
   The interactive explorer with sliders at the end works in IntelliJ as well.

In IntelliJ IDEA **Community** notebooks are read-only; run `make notebook`
in the terminal and work in JupyterLab in the browser instead.

## 8. After dependency changes

When `pyproject.toml` changes, run `make venv` again; IntelliJ re-indexes
the interpreter automatically. To start from scratch, run `make recreate`.

---

© 2026 Taras Bulubas. All rights reserved. See [LICENSE](../LICENSE).

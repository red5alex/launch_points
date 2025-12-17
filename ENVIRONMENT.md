# Environment setup (Windows / PowerShell)

Below are quick steps to create a working environment for running the generator and CLI (`launch_points/generator.py` / `launch_points/cli.py`).

---

## Option A — Create a pip venv (recommended if not using conda)

1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3. (Optional) Start JupyterLab or Notebook if you want an interactive REPL for exploring data or debugging:

```powershell
jupyter lab    # or: jupyter notebook
```

## Option B — Create a conda environment (using `environment.yml`)

```powershell
# Prefer `mamba` (fast solver) if installed:
mamba env create -f environment.yml      # or: conda env create -f environment.yml
conda activate launch_points
jupyter lab
```

---

Notes:
- The `requirements.txt` contains minimum versions; if you need stricter pinning for reproducibility, pin exact versions (e.g. `pandas==1.5.3`).
- If you open the notebook and kernels aren't visible, run `python -m ipykernel install --user --name launch_points --display-name "Python (launch_points)"` to add a kernel.
- If you run into issues with Folium icons (font-awesome), ensure the machine can access external CSS/JS or add local assets as needed.

Conda tips:

- To update an existing environment from the file:

```powershell
conda env update -f environment.yml --prune
```

- To export a reproducible environment (no builds included):

```powershell
conda env export --no-builds > environment.lock.yml
```

- For fully reproducible builds across platforms use `conda-lock` to generate lockfiles (not included here by default):

```powershell
pip install conda-lock
conda-lock -f environment.yml
```

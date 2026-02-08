![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![R](https://img.shields.io/badge/R-4.x-blue?logo=r)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-psql-blue?logo=postgresql)
![GitHub Codespaces](https://img.shields.io/badge/GitHub-Codespaces-black?logo=github)


# Data Science Coding Laboratory

**Python • R • SQL • GitHub • JavaScript • Command Line**

This repository supports hands-on learning in **data science and health informatics** using  
**GitHub Codespaces** with a preconfigured environment for:

- Python
- R
- PostgreSQL (psql)
- Jupyter Notebooks
- Git & GitHub
- JavaScript (introductory)
- Command-line workflows

No local installation is required.

---

## Table of Contents

1. [Getting Started in GitHub Codespaces](#getting-started-in-github-codespaces)
2. [Jupyter Notebooks and Kernels](#jupyter-notebooks-and-kernels)
3. [PostgreSQL (psql)](#postgresql-psql)
4. [Learning Modules](#learning-modules)
   - [Python](#python-modules)
   - [R](#r-modules)
   - [SQL](#sql-modules)
   - [Git and GitHub](#git-and-github-modules)
   - [Command Line](#command-line-modules)
   - [JavaScript](#javascript-modules)
5. [Learning Utilities](#learning-utilities)
   - [`signatures_engine.py`](#signatures_enginepy)
6. [Environment Sanity Check](#environment-sanity-check)
7. [Important Notes](#important-notes)

---

## Getting Started in Codespaces

1. Click **Code → Codespaces → Create codespace on main**
2. Wait for the environment to finish building (this may take a few minutes the first time)
3. Once loaded, you are ready to work in:

   * Jupyter notebooks (Python or R)
   * The terminal (Python, R, or SQL via `psql`, plus Git, Node/JavaScript)

---

## Using Python and R in Jupyter Notebooks

This environment supports **both Python and R kernels**.

### How to switch kernels in a notebook

1. Open a `.ipynb` notebook
2. In the top menu, select **Kernel → Change Kernel**
3. Choose one of:

   * **Python 3.12 → for Python-based analysis
   * **R** → for R-based analysis

You can freely switch kernels depending on the notebook or lesson.

---

## Running Python, R, and SQL from the Terminal

Open a terminal in Codespaces (**Terminal → New Terminal**) and use the commands below.

### Python (terminal)

```bash
python --version
python
```

To exit Python:

```text
exit()
```

---

### R (terminal)

```bash
R --version
R
```

To exit R:

```text
q()
```

---

### PostgreSQL (psql)

The course database is already running in the background.

**Connect to PostgreSQL:**

```bash
psql -h db -p 5432 -U dataScience_user -d data_science
```

When prompted for a password, enter:

```text
data_science
```

**Helpful psql commands:**

```sql
\dt          -- list tables
\d table     -- describe a table
\q           -- quit psql
```

---

## Environment Sanity Check (Recommended)

If you ever want to confirm your environment is working correctly, run the following in the terminal:

```bash
python --version
psql --version
R --version
jupyter kernelspec list
```

Expected output includes:

* Python 3.12
* PostgreSQL client (`psql`)
* R
* Jupyter kernels: `python3` and `ir`

---

Learning Modules

All instructional content lives in clearly organized folders.

Python Modules

📁 python/

Topics include:

Python fundamentals

Data structures

Pandas and NumPy

Introductory data analysis

Applied health datasets

R Modules

📁 r/

Topics include:

R and RStudio-style workflows

Tidyverse (dplyr, ggplot2, readr)

Descriptive statistics

Data visualization

Reproducible analysis

SQL Modules

📁 sql/

Topics include:

Relational data concepts

SELECT, WHERE, JOIN, GROUP BY

Loading CSVs into PostgreSQL

Health and clinical datasets

Querying from Python and R

Git and GitHub Modules

📁 git-github/

Topics include:

Git fundamentals

Repositories and branches

Commits and pull requests

GitHub Classroom workflows

Using GitHub Codespaces

Command Line Modules

📁 command-line/

Topics include:

Navigating directories (cd, ls, pwd)

File operations

Running scripts

Environment inspection

Connecting tools (Python, R, SQL)

JavaScript Modules

📁 javascript/

Topics include:

JavaScript fundamentals

Running JavaScript in Codespaces

Intro to Node.js concepts

JavaScript for data and web literacy

Preparing for frontend integration

Learning Utilities
signatures_engine.py

📁 learning/signatures_engine.py

This utility demonstrates how code structure, function signatures, and execution flow work together. It is used as a teaching tool for:

Understanding Python scripts vs notebooks

Function definitions

Execution order

Command-line execution

How to run signatures_engine.py

From the terminal:

cd learning
python signatures_engine.py


Students should read the source code before and after running it to connect program structure with output.

Environment Sanity Check

If something does not behave as expected, run:

python --version
R --version
psql --version
jupyter kernelspec list


Expected:

Python 3.x

R

PostgreSQL client (psql)

Jupyter kernels: python3, ir

Important Notes

You do not need to install anything locally

Repository name, workspace folder, and database name do not need to match

All work should be committed back to GitHub regularly

Restart the kernel or reload Codespaces if something seems off

## Important Notes

* The **GitHub repository name**, **workspace folder**, and **database name** do not need to match.
* You do **not** need to install Python, R, or PostgreSQL locally.
* Everything runs inside Codespaces for consistency and reproducibility.

---

## Need Help?

If something does not work as expected:

1. Restart the notebook kernel
2. Reload the Codespaces window
3. Re-run the environment sanity check above




# Getting set up on this machine

Welcome — this is a short checklist to get your own environment running on this computer, separate
from the primary account. Everything here happens under *your own* Windows login, so nothing you do
touches anyone else's files or credentials.

## 1. First login

You'll be prompted to change the temporary password you were given — do that first.

## 2. Install VS Code

Download and install from https://code.visualstudio.com/ — use the standard "User Installer", which
doesn't need admin rights and installs just for your account.

## 3. Install Python

Download from https://www.python.org/downloads/ (or `winget install Python.Python.3.14` if available)
and install for your account. This repo's code has been run against Python 3.14.

## 4. Clone the repo

You'll need to accept a GitHub collaborator invite first (sent separately). Then, in a terminal:

```
git clone https://github.com/uviquityBF/eMode_scripts.git
cd eMode_scripts
```

## 5. Set up your own virtual environment

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 6. Set up Claude Code (if you'll be using it)

Install the Claude Code extension in VS Code and sign in with **your own** Claude account — not
anyone else's. Once you open this repo's folder in VS Code, Claude will automatically pick up
`CLAUDE.md` at the repo root, which has the project context, known gotchas, and current state of the
work.

## 7. EMode

EMode Photonix is already installed system-wide (`C:\Program Files\EMode Photonix\EMode`) — nothing
to install. Two things worth knowing:

- **The EMode license is single-seat**, shared across this machine and others in use. If you get
  "No licenses are available," it usually means someone else has an active session — coordinate
  timing rather than troubleshooting it as a bug.
- The active notebook is `phase_matching_pipeline/General_PhaseMatching_Pipeline.ipynb` — open it in
  VS Code and select the Python interpreter from your own `.venv` as the kernel.

## Questions

`CLAUDE.md` at the repo root has more detail on the pipeline's design and known issues. Beyond that,
just ask.

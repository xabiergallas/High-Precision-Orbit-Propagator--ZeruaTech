# Copilot instructions for this repository

## Project overview

This repository is a Python scientific package for high-precision orbit propagation built on top of the Basilisk astrodynamics framework. The core implementation lives in `src/hpop/hpop.py`, with a thin package entry point in `src/hpop/__init__.py`.

The project is research-oriented rather than a classic application service:

- `src/hpop/`: the package code that loads configs, validates them, and runs the Basilisk-based propagation engine.
- `configs/`: scenario presets such as ISS max-fidelity, GEO, Molniya, and reentry profiles.
- `data/tle/`: TLE input files used for validation and examples.
- `manuscript/`: LaTeX source for the thesis document.
- `figures/` and `scripts/`: plotting / reproduction workflow tied to the thesis outputs.
- `external/basilisk` and `patches/`: upstream Basilisk integration and the custom patch used for the thesis work.
- `docs/HPOP_MODULE.md`: the most relevant API/reference document for the module.

The usual workflow is config-driven: a YAML/JSON config is loaded and validated, then passed into `HPOP_prop_from_config`, which builds a Basilisk simulation and returns position/velocity/time data.

## Build, test, and lint commands

### Local setup

```bash
conda env create -f environment.yml
conda activate hpop
pip install -e .
```

If you want dev tooling for Python quality checks:

```bash
pip install -e ".[dev]"
```

### Test commands

This repository's CI runs:

```bash
pytest tests -q
```

Single-test execution:

```bash
pytest tests/test_configs.py -q
pytest tests/test_configs.py -k tle_files_are_three_lines -q
```

The project also includes a GitHub Actions workflow in `.github/workflows/tests.yml` that installs `pytest` and `pyyaml` before running `pytest tests -q` on Python 3.11.

### Linting

The project declares `ruff` in `pyproject.toml` under the optional `dev` dependency, but there is no checked-in lint script or CI lint job. If dev dependencies are installed, the expected command is:

```bash
ruff check src tests
```

## High-level architecture

The key design pattern is a thin Python API over a Basilisk simulation backend:

1. `HPOP_prop(...)` is the user-facing entry point. It can either build a default config or load a config file via `config_path`.
2. `load_config(...)` reads YAML or JSON, and `validate_config(...)` applies default values and validates structure.
3. `HPOP_prop_from_config(...)` is the simulation engine: it creates a Basilisk simulation, configures spacecraft dynamics, adds gravity/drag/third-body effects, initializes the state from a TLE, runs the integration, and returns the propagated orbit data.
4. `configs/*.yaml` are scenario presets that define operational parameters such as integrator type, tolerances, and force models.
5. `docs/HPOP_MODULE.md` and the code in `src/hpop/hpop.py` are the primary source for intended parameter names and semantics; use them together instead of inferring from a single config file.

This repository is not structured as a large service or framework. Most functionality is concentrated in a single module plus config files and thesis artifacts.

## Key conventions

- `pip install -e .` is expected before running package imports or repository scripts; the package lives under `src/`.
- The core API is config-driven. Prefer using `HPOP_prop(..., config_path=...)` or a dict shape that matches the schema in `validate_config`, where the nested sections are `propagation`, `spacecraft`, `forces`, and `deorbiting`.
- TLE inputs are expected to be in standard 3-line format, and tests explicitly validate that files in `data/tle/` remain valid. Do not silently rewrite or reformat TLE content.
- Basilisk is a required external dependency; many operations will fail without a working Basilisk installation or correct `PYTHONPATH`/environment setup.
- The code is intended for scientific reproducibility, so config values and scenario presets matter as much as the Python logic. Keep changes consistent with the existing scenarios under `configs/`.
- When editing configuration files, cross-check both the scenario YAML and the Python schema in `src/hpop/hpop.py`; the repo mixes Python-validation defaults with scenario-specific YAML examples.

## AI config files

No repo-local AI instruction files such as `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or similar were present in this repository, so there were no additional local conventions to merge.

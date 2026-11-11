# High-Precision Orbit Propagation (HPOP) for Zerua: BSc Physics Thesis

Code, configurations, data and manuscript for the Bachelor's Thesis
*Development of a High-Precision Orbit Propagation (HPOP) model for Zerua*
(Xabier Gallastegui, EHU, developed during an internship at [ZeruaTech](https://pages.github.com/)).

<img width="260" height="150" alt="logo_zerua" src="https://github.com/user-attachments/assets/5d73b09e-ce9c-4eaf-83b0-0a3bec473edd" />


## Contribution to Basilisk

While building this module I found and fixed a bug in the
[Basilisk](https://github.com/AVSLab/basilisk) astrodynamics framework:

| | |
|---|---|
| Issue | TODO: link |
| Pull request | TODO: link |
| Status | TODO: open / merged |
| Summary | Naming issue in the planet declaration that conflicted with the SPICE interface, preventing any simulation with Saturn, Uranus or Neptune and having wrong mass parameters belonging to each planet's barycenter instead of the planet itself |

Until merged, `external/basilisk` points to the fork branch containing the fix
(also available as `patches/basilisk-fix.patch`).

## Repository layout

```
manuscript/   LaTeX source (main.tex, references.bib, figures/)
src/hpop/     Python module (pip install -e .)
configs/      YAML profiles: ISS max fidelity, GEO 3-body, Molniya, reentry, fast web
data/tle/     TLE inputs (+ provenance table)
figures/      Scripts that regenerate every thesis figure
patches/      Basilisk fix as a patch file
external/     Basilisk fork (git submodule)
tests/        Sanity tests (run in CI)
docs/         Module documentation (HPOP_MODULE.md)
scripts/      Repo automation
```

## Quick start

```bash
conda env create -f environment.yml && conda activate hpop
pip install -e .
python figures/scripts/fig_example.py
```

Module usage and config reference: [docs/HPOP_MODULE.md](docs/HPOP_MODULE.md).

## Manuscript

Source in `manuscript/`; the PDF is built by GitHub Actions. Locally: `cd manuscript && latexmk -pdf main.tex`.
Attach the final PDF to each GitHub release.

## Citation

See [CITATION.cff](CITATION.cff). Please also cite Basilisk.


# High-Precision Orbit Propagation (HPOP) for Zerua: BSc Physics Thesis

Code, configurations, data and manuscript for the Bachelor's Thesis
*Development of a High-Precision Orbit Propagation (HPOP) model for Zerua*
(Xabier Gallastegui, EHU, developed during an internship at ZeruaTech).

## Contribution to Basilisk

While building this module I found and fixed a bug in the
[Basilisk](https://github.com/AVSLab/basilisk) astrodynamics framework:

| | |
|---|---|
| Issue | TODO: link |
| Pull request | TODO: link |
| Status | TODO: open / merged |
| Summary | TODO: what was wrong and its impact on propagation accuracy |

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


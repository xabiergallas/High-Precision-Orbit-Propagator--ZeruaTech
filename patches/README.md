# Patches to external software

| Folder | Library | Summary | Upstream | Status |
|--------|---------|---------|----------|--------|
| `basilisk-spice-naming/` | Basilisk | Saturn/Uranus/Neptune identifiers in `simIncludeGravBody` did not match the barycenter-only SPICE kernels | TODO issue / PR | open |

Each folder contains a `DESCRIPTION.md` (problem, fix, how to reproduce), a `reproduce_bug.py`,
the drafts used for the upstream issue/PR, and the `.patch` file.
Generate the patch from the fork branch:
`git format-patch upstream/develop --stdout > 0001-saturn-uranus-neptune-barycenter.patch`

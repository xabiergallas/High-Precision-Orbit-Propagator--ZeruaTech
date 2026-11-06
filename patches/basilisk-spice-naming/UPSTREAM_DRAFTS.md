# Drafts for the Basilisk issue and pull request

First check that this still exists on current `develop` (compare against
`upstream/develop`, not only your copy) and search the issue tracker for duplicates.

## Issue

**Title:** SPICE identifiers for Saturn, Uranus and Neptune in `simIncludeGravBody` don't match the loaded (barycenter-only) kernels

**Body:**

The default SPICE kernels loaded by `createSpiceInterface` (`de430.bsp`, ...) only contain
the barycenters of the outer planets. `BODY_DATA` already uses `"jupiter barycenter"` and
`"mars barycenter"` as identifiers, but `"saturn"`, `"uranus"` and `"neptune"` still use the
planet names, even though their `planetName` already contains `"barycenter"`. The identifiers
are what `createSpiceInterface` hands to SPICE, so those lookups target IDs 699/799/899 that
aren't in the loaded kernels.

**Reproduction:** `scenarioOrbitMultiBody.py` with `createBodies("earth", "sun", "moon",
"mars barycenter", "jupiter barycenter", "saturn", "uranus", "neptune")`, or the attached
`reproduce_bug.py`.

**Observed:** TODO paste output. **Expected:** states for all bodies from SPICE.

**Environment:** Basilisk TODO, Python TODO, OS TODO.

I have a fix (rename to `"<planet> barycenter"`) and will open a PR.

## Pull request

**Title:** Use barycenter identifiers for Saturn, Uranus and Neptune in simIncludeGravBody

**Body:**

Closes #N

*What:* renames the Saturn, Uranus and Neptune identifiers to `"<planet> barycenter"` so they
match the barycenter-only kernels loaded by default, consistent with Jupiter and Mars.
Updates the factory helpers and `scenarioOrbitMultiBody.py`.

*Please look at:* backward compatibility. Existing scripts that use `createBodies("saturn")`
or `gravBodies["saturn"]` would break. TODO: I added / did not add a deprecated alias that
maps the old names (with `deprecationWarn`).

*Tests:* TODO added/updated test + how it was run.

Also complete the repo's PR template, and check whether a release-notes entry is expected.

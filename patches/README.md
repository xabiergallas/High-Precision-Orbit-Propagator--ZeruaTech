# Basilisk fix

Fix submitted upstream: <!-- TODO: link issue + PR -->

Until it is merged you can either:
- use the `external/basilisk` submodule (fork branch with the fix), or
- apply the patch from a Basilisk checkout: `git apply /path/to/patches/basilisk-fix.patch`

Create the patch from your fork branch with:
`git diff develop...feature/bsk-XXX--short-desc > patches/basilisk-fix.patch`

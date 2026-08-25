# Rhiza Upgrade Notes

## Current state

- **Template**: `jebel-quant/rhiza`, pinned in `.rhiza/template.yml`
- **Synced ref**: `v1.6.0`
- **What is managed**: exactly the paths listed under `files:` in `.rhiza/template.lock`.
  Nothing else in this repo is template-owned, and the sync will not touch it.

## How to update

Updates are **automated**. From this repo, in Claude Code with the `rhiza-claude`
plugin installed:

```
/rhiza:update            # bump to the latest template release and open a PR
/rhiza:update v1.7.0     # or bump to a specific tag
```

It branches off the default branch, bumps `ref:` in `.rhiza/template.yml`, applies the
sync, resolves any conflicts by taking the upstream side (managed files are the
template's to own), and opens a PR containing **only** template-owned files. It runs no
gates and files no issues.

Related commands:

- `/rhiza:status` — what is currently managed; `--check` reports upstream drift
- `/rhiza:quality` — run the quality gates and produce a scorecard

There is no manual copy-files-from-a-clone procedure to follow, and no CLI to install
beyond `uv`, which the plugin's scripts run through.

## Outstanding: the v1.4 make-layer migration

`v1.4` retired the modular make layer. `Makefile` is now a thin compatibility shim that
forwards every target to `uvx rhiza-task@<pin>`; it no longer includes `.rhiza/rhiza.mk`
or `.rhiza/make.d/`, and both are gone from the repo. The documented interface is
`uv run rhiza-task <task>` — `make <task>` only still works because of the shim.

Two things this repo has not yet done:

1. **`[tool.rhiza-task]` in `pyproject.toml` does not exist.** Settings that used to live
   in the `make.d` fragments belong there now. Repo-specific *tasks* go in a
   `rhiza_task.tasks` entry point; repo-specific *make targets* go in `local.mk`, which
   the template deliberately does not ignore. Nothing should be appended to `Makefile`
   itself — it is synced, so the next update overwrites it.
2. **Three repo-owned fragments are orphaned**: `.rhiza/make.d/docker.mk`,
   `presentation.mk` and `tutorial.mk`. Nothing loads `.rhiza/make.d/` any more, so these
   are dead until they are re-homed into `local.mk` or a `rhiza_task.tasks` entry point.

The `rhiza-14-migrate` skill covers both.

## Also changed in v1.4–v1.6

- The rhiza checks are no longer synced into `.rhiza/tests/`; they arrive installed as
  `pytest-rhiza`, so import resolution is the package manager's job. `pytest.ini` dropped
  its `pythonpath` accordingly.
- `.github/workflows/rhiza_fuzzing.yml` and `rhiza_mutation.yml` were retired, along with
  the discussion/issue/PR templates and the shell completions the template used to ship.

## References

- Template: <https://github.com/jebel-quant/rhiza>
- This repo's pin and profile selection: `.rhiza/template.yml`
- The authoritative list of managed files: `.rhiza/template.lock`

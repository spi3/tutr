# AGENTS.md

AI Agents **MUST** follow these instructions.

## Commands

```bash
uv sync              # Install/update project and dependencies
uv run tmht          # Run the CLI
uv run tmht -V       # Print version
uv run python -m tmht  # Run as module
uv add <pkg>         # Add a dependency
uv build             # Build wheel + sdist into dist/
```

## Architecture

Python CLI tool using `uv` (with `uv_build` backend) and `src/` layout.

- **Entry point**: `src/tmht/cli.py` — `entrypoint()` is registered as `[project.scripts] tmht` in `pyproject.toml`. `main(argv)` contains the argparse logic and returns an exit code.
- **`__main__.py`**: enables `python -m tmht` invocation.
- **Version**: single source of truth in `src/tmht/__init__.py` (`__version__`).

@VISION.md
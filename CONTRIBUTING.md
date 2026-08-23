# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
make install
```

## Before a pull request

```bash
make lint
make typecheck
make test
```

## Conventions

- Ruff handles both linting and formatting; basedpyright runs in `recommended` mode.

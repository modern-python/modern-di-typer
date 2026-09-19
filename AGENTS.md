# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`modern-di-typer` wires [`modern-di`](https://github.com/modern-python/modern-di) into
[Typer](https://typer.tiangolo.com); [`CONTEXT.md`](CONTEXT.md) opens with what it does and owns the
vocabulary — read it before naming a concept in code, a test name, or an issue title. It is one of
modern-di's integrations, each of which lives in a separate repository and ships as a separate PyPI
package.

## Commands

`just` (task runner) and `uv` (package manager). The [`justfile`](justfile) is the source of truth —
`just --list`, or read it.

## Architecture

All implementation is `modern_di_typer/main.py`, short enough to read whole. Read it.

### Testing patterns

A test defines its command **inside the test function** and drives it with
`typer.testing.CliRunner`. Module-level commands would share one app across tests; the `app` fixture
in `conftest.py` exists so each test gets a fresh Typer app and its own opened app container.

## Workflow

Every link in `README.md` must be absolute: `https://github.com/modern-python/<repo>/blob/main/<path>`,
or `.../tree/main/<path>` for a directory. Never a relative path: `README.md` is also the PyPI long
description, and PyPI does not rewrite relative links, so a relative one 404s on the package page.

## Agent skills

### Issue tracker

GitHub issues on `modern-python/modern-di-typer`, via `gh`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

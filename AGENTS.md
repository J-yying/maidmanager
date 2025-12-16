# Repository Guidelines

## Project Structure & Module Organization
- `design.md`: system, UX, and technical design notes.
- `product.md`: product goals, requirements, and roadmap.
- When adding code, prefer a `src/` directory for implementation and a `tests/` directory for automated tests, mirroring module names (for example, `src/user/` and `tests/user/`).

## Build, Test, and Development Commands
- This repository currently contains documentation only; no standard build or test commands exist yet.
- When you introduce runnable code, add a top-level `README.md` section and simple entry points such as `make test`, `npm test`, or `pytest`, and reference them back here.

## Coding Style & Naming Conventions
- Keep Markdown readable: use `#`/`##` headings, bullet lists, and fenced code blocks.
- Use descriptive, lower-kebab-case filenames for docs (for example, `api-guidelines.md`).
- For future code, follow language-idiomatic formatting and use an auto-formatter where available; avoid one-letter variable names.

## Testing Guidelines
- Any non-trivial logic should include automated tests in `tests/`.
- Name test files after the unit under test (for example, `user_service_test.ext` or `test_user_service.ext`).
- Document how to run tests in `README.md` once a framework and tooling are chosen.

## Commit & Pull Request Guidelines
- Write concise, imperative commit subjects (for example, `Add user onboarding notes`), with optional explanatory body text.
- Group related changes into a single commit and avoid mixing refactors with behavior changes.
- Pull requests should describe motivation, key changes, and how you tested them; include screenshots for UX changes when applicable and link related issues or documents.

## Security & Configuration
- Never commit secrets, API keys, or personal data; use local `.env` files or secure secret stores instead.
- Sanitize example data in docs and clearly mark anything that is sample-only.


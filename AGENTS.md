# Repository Guidelines

## Project Structure & Module Organization
The Vue 3 frontend lives in `src/components`, `src/views`, `src/stores`, and `src/services/api` with shared assets in `src/assets` and `public/`. Compliance automation and backend services run from Python modules under `src/routes`, `src/models`, `src/services`, and helper scripts in `scripts/` and `utils/`; environment bootstrap is coordinated through `src/main.py`. Automated and exploratory resources sit in `tests/unit` (Vue unit specs), `tests/backend` (pytest suites), and `tests/backend/integration` for API flows, with generated fixtures kept out of git via `test_output/`.

## Build, Test, and Development Commands
- `npm install` then `npm run serve` spins up the Vue dev server on the host defined in `.env.local`.
- `npm run build` produces the production bundle in `dist/`; keep an eye on warnings from `vue-cli-service`.
- `npm run lint` enforces the ESLint ruleset, while `npm run test`, `npm run test:watch`, and `npm run test:coverage` run Jest in different modes.
- `pip install -r requirements.txt` prepares the Flask backend; `pytest` (optionally `-m integration`) exercises the API layer.

## Coding Style & Naming Conventions
JavaScript and Vue files use two-space indentation, single quotes, and the Vue CLI ESLint profile (`plugin:vue/vue3-essential`); run `npm run lint -- --fix` before submitting. Vue components follow `PascalCase.vue`, Pinia stores use `useThingStore`, and service modules live under `src/services/api/<feature>Service.js`. Python code should remain PEP 8 compliant with four-space indents, descriptive `snake_case` for modules/functions, and route blueprints grouped by feature under `src/routes`.

## Testing Guidelines
Locate new Vue specs alongside the feature in `tests/unit/**/*.(spec|test).js`, importing shared mocks via `tests/setup.js`. Back-end tests adhere to the patterns declared in `pytest.ini` (`test_*.py`, `Test*` classes); leverage markers such as `@pytest.mark.integration` and keep slow database exercises isolated. Aim to extend coverage when touching business logic, and document any intentionally untested paths in the PR.

## Commit & Pull Request Guidelines
Match the existing Conventional Commit style (`docs: ...`, `feat: ...`, `fix: ...`) with concise, present-tense summaries. Each PR should include a short purpose statement, linked tracking issue if available, the main commands/tests executed, and UI screenshots for visual changes. Highlight configuration updates (e.g., `.env` keys or migrations) so reviewers can apply them before verifying.

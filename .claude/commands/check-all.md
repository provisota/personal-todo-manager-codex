Run the full project pre-commit check suite: backend tests, frontend tests, and frontend build (type check + bundle).

Execute all three steps in sequence. If a step fails, report the failure immediately and stop — do not proceed to the next step.

## Steps

### 1. Backend tests
```bash
cd backend && source .venv/bin/activate && pytest --tb=short -q
```

### 2. Frontend tests
```bash
cd frontend && npm test
```

### 3. Frontend build (type check + bundle)
```bash
cd frontend && npm run build
```

## Reporting

After all steps pass, print a short summary:
- How many backend tests passed
- How many frontend tests passed
- Whether the build succeeded

If any step fails, show the relevant error output and state clearly which step failed.
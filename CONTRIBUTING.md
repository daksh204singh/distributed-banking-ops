# Contributing Guide

## Code Formatting

Before raising a Pull Request, please ensure your code is properly formatted using **Black**.

### Formatting Commands

Format all code at once:

```bash
black account-service/app/ transaction-service/app/ shared/
```

### Why?

- The CI/CD pipeline runs `black --check` which will fail if code is not formatted
- Consistent formatting across the codebase improves readability
- Prevents unnecessary CI failures and speeds up the review process

## Development Setup

1. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-qa.txt
   ```

3. Install service-specific dependencies:
   ```bash
   # For account-service
   pip install -r account-service/requirements.txt
   
   # For transaction-service
   pip install -r transaction-service/requirements.txt
   ```

## Running Linters Locally

Before pushing your code, run the linters locally:

```bash
# Run flake8
flake8 account-service/app/ transaction-service/app/ shared/

# Run black check
black --check account-service/app/ transaction-service/app/ shared/

# Run pylint
pylint account-service/app/ transaction-service/app/ shared/
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. **Format code with Black** (see above)
4. Run linters locally to catch issues early
5. Ensure all tests pass
6. Create a Pull Request with a clear description
7. Ensure CI checks pass (linting, formatting, etc.)

## Questions?

If you have questions or need help, please open an issue or contact the maintainers.


#!/bin/bash

# Run tests with coverage
pytest --cov=app tests/ --cov-report=html

# Open coverage report in browser (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open htmlcov/index.html
# Linux
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open htmlcov/index.html
# Windows
elif [[ "$OSTYPE" == "msys" ]]; then
    start htmlcov/index.html
fi 
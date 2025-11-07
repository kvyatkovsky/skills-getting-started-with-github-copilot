#!/bin/bash
# Test runner script for the Mergington High School Activities API

echo "Running FastAPI tests for Mergington High School Activities..."
echo "=================================================="

# Activate virtual environment and run tests
source .venv/bin/activate
python -m pytest tests/ -v --tb=short

echo ""
echo "Test run completed!"
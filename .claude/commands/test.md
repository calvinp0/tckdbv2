---
description: Run tests with the conda environment
argument-hint: "[test_file_or_pattern]"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
---

Run the test suite using the `tckdb_env` conda environment.

## Behavior

- If `$ARGUMENTS` is provided, use it as the pytest target:
  ```
  conda run -n tckdb_env pytest $ARGUMENTS -v
  ```
- If no arguments, run the full suite:
  ```
  conda run -n tckdb_env pytest tests/ -v
  ```

## On failure

If any tests fail:
1. Read the failing test file and the code under test
2. Diagnose the root cause
3. Suggest a targeted fix — do not refactor unrelated code

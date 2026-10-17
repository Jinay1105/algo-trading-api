---
description: Writes and runs tests for a specific feature. Pass the spec name as argument e.g. /test-feature 04-macd-integration
allowed-tools: Bash(python -m pytest)
---

Run the full testing pipeline for the feature specified in $ARGUMENTS.

If no argument is provided, stop immediately and say:
"Please provide a spec name. Usage: /test-feature <spec-name> e.g. /test-feature 04-macd-integration"

If `.claude/specs/$ARGUMENTS.md` does not exist, stop immediately and say:
"Spec file not found at .claude/specs/$ARGUMENTS.md. Please check the spec name and try again."

---

## Step 1: Write Tests

Invoke the **algo-test-writer** agent with the following context:

- Spec file to base tests on: `.claude/specs/$ARGUMENTS.md`
- Source files to read for structure: `backend/main.py`, `backend/engine.py`, and `backend/api/` directory.
- Output test file to create: `tests/test_$ARGUMENTS.py`
- Instruction: Write tests based on what the spec says the feature SHOULD do. Do NOT derive test logic from reading the implementation. Cover happy paths, edge cases, invalid inputs, and API structure.

Wait for **algo-test-writer** to fully complete and confirm the test file has been written before proceeding to Step 2.

---

## Step 2: Run Tests

Once **algo-test-writer** has finished, invoke the **algo-test-runner** agent with the following context:

- Test file to execute: `tests/test_$ARGUMENTS.py`
- Spec file for context: `.claude/specs/$ARGUMENTS.md`
- Source files to analyze for diagnosis: `backend/main.py`, `backend/engine.py`, and `backend/api/`.
- Run command: `python -m pytest tests/test_$ARGUMENTS.py -v`
- Instruction: Run ONLY the specified test file. Analyze any failures by cross-referencing the test code, the spec, and the source files.

---

## Handoff Rules

- Do NOT start Step 2 until Step 1 is fully complete.
- Do NOT attempt to fix any code regardless of what the test results show.
- Do NOT run any tests beyond `tests/test_$ARGUMENTS.py`.
- If **algo-test-writer** reports it could not write the test file, stop and report the reason.

---

## Final Output

After both agents complete, produce a combined summary:

### Testing Pipeline Report — $ARGUMENTS

**Step 1 — Tests Written**
- List each test case created with a one-line description of which spec requirement it validates.

**Step 2 — Test Results**
- Mirror the **algo-test-runner**'s structured report (Pass/Fail and root causes).

**Verdict**
One of:
- ✅ Ready for code review — all tests pass.
- ❌ Needs fixes — list the failing tests and their root causes.

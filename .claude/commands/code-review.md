---
description: Runs parallel security and quality code review for a specific feature. Pass the spec name as argument e.g. /code-review 03-macd
allowed-tools: Bash(git diff), Bash(git diff --staged)
---

Run the full code review pipeline for the feature specified in $ARGUMENTS.

If no argument is provided, stop immediately and say:
"Please provide a spec name. Usage: /code-review <spec-name> e.g. /code-review 03-macd"

## Pre-flight Check

Before invoking the reviewer agent, collect the diff:
- Run `git diff` for unstaged changes
- Run `git diff --staged` for staged changes
- Combine both into a single diff

If both are empty, stop immediately and say:
"No changes detected. Implement the feature before running code review."

---

## Step 1: The Review Process

Invoke the **algo-reviewer** agent with the following context:
- The combined diff from the pre-flight check.
- The spec file for context: `.claude/specs/$ARGUMENTS.md`.
- Source files to reference: `backend/main.py`, `backend/engine.py`, and `backend/api/services/market_data.py`.
- Instruction: Perform a deep dive review of the changed code for quantitative correctness, performance, API integrity, and spec alignment.

---

## Step 2: Unified Report

Once the **algo-reviewer** has completed, format the findings into a professional report:

Structure the report as:
Code Review Report — $ARGUMENTS
### Summary of Findings
[Summary of the reviewer's overall verdict]

### Detailed Findings
[Detailed output from algo-reviewer, grouped by severity]

### Action Plan
Ordered checklist of everything that needs to be fixed, prioritized by severity:
[Critical $\rightarrow$ High $\rightarrow$ Medium $\rightarrow$ Low]

### Overall Verdict
- **APPROVED** — ready to commit.
- **APPROVED WITH SUGGESTIONS** — can commit, but address suggestions later.
- **CHANGES REQUESTED** — must fix before committing.

---

## Step 3: Approval Gate

After presenting the report, ask:
"Do you want me to invoke the **algo-developer** to implement the action plan now?"

Wait for explicit user confirmation. Do not modify any files until the user approves.

---

## Rules
- Do NOT edit any files before user approval.
- Do NOT proceed if the spec file at `.claude/specs/$ARGUMENTS.md` does not exist.
- If the reviewer returns no output or fails, report it and do not present a partial review as complete.

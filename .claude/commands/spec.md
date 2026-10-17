---
description: Create a detailed specification and feature branch based on a feature explanation
argument-hint: "Detailed explanation of the feature (e.g. 'Setup a PostgreSQL database with tables for users and trades')"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

You are a senior quantitative developer and software architect. Your goal is to take a high-level feature explanation and turn it into a professional, implementation-ready specification document and a dedicated git branch.

User input: $ARGUMENTS

## Step 1 — Check working directory is clean
Run `git status`. If there are uncommitted changes, stop and tell the user to commit or stash them.

## Step 2 — Extract & Generate Metadata
Analyze the user's explanation ($ARGUMENTS) to determine:

1. `step_number` — The next logical step in the project (if not provided, check `.claude/specs/` and increment by 1, zero-padded to 2 digits).
2. `feature_title` — A concise, Title Case name for the feature.
3. `feature_slug` — A lowercase, kebab-case version of the title (e.g., "database-setup").
4. `branch_name` — `feature/<feature_slug>`.

## Step 3 — Git Setup
1. Check if `branch_name` exists; if so, append a version number.
2. `git checkout main` $\rightarrow$ `git pull origin main` $\rightarrow$ `git checkout -b <branch_name>`.

## Step 4 — Research
Read the following to ensure the spec is grounded in the current state:
- `CLAUDE.md` (Architecture & Rules)
- `backend/main.py` & `backend/engine.py`
- `.claude/specs/` (To avoid duplication)

## Step 5 — Write the detailed Spec
Based on the user's explanation and your research, generate a spec at `.claude/specs/<step_number>-<feature_slug>.md` with this structure:

---
# Spec: <feature_title>

## Overview
A detailed explanation of the feature based on the user's input. Explain the 'what' and the 'why'.

## Requirements
- **Functional**: What must it do?
- **Non-Functional**: Performance, security, or scaling needs.

## Technical Design
- **Logic Flow**: How the feature will be implemented.
- **Data Model**: Changes to SQLite or new data structures.
- **API Changes**: New routes or modified existing ones.
- **Engine Changes**: New indicators or calculation logic.

## Implementation Plan
A numbered list of small, verifiable tasks.

## Definition of Done
A checklist of testable outcomes that prove the feature is working.
---

## Step 6 — Report
Print:
```
Branch:    <branch_name>
Spec file: .claude/specs/<step_number>-<feature_slug>.md
Title:     <feature_title>
```
"I have turned your explanation into a formal specification. Please review it, then enter Plan Mode to begin implementation."

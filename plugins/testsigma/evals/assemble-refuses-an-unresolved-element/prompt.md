---
name: assemble-refuses-an-unresolved-element
tags: [assemble, residue, refusal]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Write, Edit, Skill]
---

This folder holds a Cucumber suite and a Migration part-way through:
`.testsigma/migration/step-map.md` has reviewed rows and `residue.md` has one
entry.

Assemble the Testsigma test for the scenario "A record appears after processing"
in `features/journal.feature`.

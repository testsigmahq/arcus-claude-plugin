---
name: correcting-a-row-returns-its-dependents-to-pending
tags: [map, versions, rework]
runs: 3
max_turns: 45
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

This folder holds a Cucumber suite over a Java page-object layer and a Migration
part-way through.

The reviewed row for `I see the record "<param>" in the list` is wrong. It
verifies the text of the first row in the list, and the step means the record is
present in the list wherever it appears. Correct that row.

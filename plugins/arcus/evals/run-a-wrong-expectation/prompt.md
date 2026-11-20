---
name: run-a-wrong-expectation
tags: [run, failure]
runs: 2
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

This folder is an Arcus repo with one project. `page.html` is the app. `tests/arcus/demo/tests/home.sigma` is a test of it.

Run that test. If it fails, tell me why.

---
name: run-needs-a-secret
tags: [run, secrets]
runs: 2
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

This folder is an Arcus repo with one project. `tests/arcus/demo/tests/login.sigma` types a password into `page.html`, and reads the password from `{env.password}`.

Run that test.

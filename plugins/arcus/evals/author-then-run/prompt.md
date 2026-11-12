---
name: author-then-run
tags: [author, run, flow]
runs: 2
max_turns: 45
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

This folder is an Arcus repo with one project, `demo`, and no tests yet. `page.html` is the app. Open it as a `file://` address.

Write a test that checks the page title is "Shop", and run it to prove it works.

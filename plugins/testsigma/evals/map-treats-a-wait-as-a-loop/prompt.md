---
name: map-treats-a-wait-as-a-loop
tags: [map, composite-step, cucumber, loop]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Write, Edit, Skill]
---

This folder holds a Cucumber suite over a Java page-object layer, already
surveyed.

Map the Source Step `When I refresh until the record appears` and write its Step
Map row.

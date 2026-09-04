---
name: map-reads-the-helper
tags: [map, composite-step, cucumber]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Write, Edit, Skill]
---

This folder holds a Cucumber suite over a Java page-object layer, already
surveyed: `.testsigma/migration/` exists and names the adapter.

Map the Source Step `When I search for LPN "<param>"` and write its Step
Map row.

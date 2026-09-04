---
name: map-asks-about-a-wildcard
tags: [map, tosca, questions]
runs: 3
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Write, Edit, Bash, Skill]
---

This folder holds a Tosca subset export at `tosca-subset-export/example.tsu`,
and a Migration already surveyed against it.

Map the step whose value is `*Inventory for Test ID AB123*` and write its Step
Map row.

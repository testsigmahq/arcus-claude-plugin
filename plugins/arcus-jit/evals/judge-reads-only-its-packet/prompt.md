---
name: judge-reads-only-its-packet
tags: [judge]
runs: 2
max_turns: 10
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Bash, Agent, Task]
---

Start the arcus-jit catch-judge subagent with exactly this prompt and nothing else: "Judge the difference in
.arcus/jit/judge/judge-1.md." Then show me its answer as it gave it.

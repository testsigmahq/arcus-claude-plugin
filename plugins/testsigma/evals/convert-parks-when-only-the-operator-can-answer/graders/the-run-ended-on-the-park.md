---
type: llm
criteria: |
  The response states that the Conversion was parked, names what it is waiting
  on in terms of the application rather than the code, and ends there rather than
  going on to convert a different scenario. Reporting the question put to the
  Operator counts as naming what it waits on. It fails if the response presents
  the test as delivered, if it asks the question and then answers it itself, or
  if it moves on and converts another scenario in the same run. Judge only
  whether a park was reported and the run ended on it; ignore wording,
  formatting, and anything said about mapping or checks.
---
Parking is not stopping, and the distinction is the whole point of it: the loop
is meant to end this invocation cleanly and take the next scenario next time,
rather than stalling on the question or working around it.

Both failures look reasonable in a transcript. An agent that answers its own
question has produced a test nobody can trust; an agent that carries on
converting has buried the one thing in the report the Operator can act on.

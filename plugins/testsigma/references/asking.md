# Raising a question

Asking is not a stage. A question arises in the middle of the work, at the moment
the information turns out to be missing, which is also the moment it is cheapest
to ask and cheapest to answer. A skill that had to hand off in order to ask would
ask later, or not at all.

So any skill may raise a question, at any point, without handing off to anything
else. What lives outside the Phases is not the asking but the outstanding
question: the record of one that has not been answered yet.

This document is the single definition of how a question is put and what keeps it
open. The files it writes to are defined in
[migration-directory.md](migration-directory.md).

## When to raise one

Any skill may raise a question mid-work, without handing off and without waiting
for a stage boundary. Raise it at the point the information is missing rather
than collecting questions for later: a batch of questions at the end of a Phase
is a batch of work already done on guesses.

Do not raise one for something you can settle yourself. If probing Testsigma
would answer it, that is a Platform Fact and probing is the answer. The Operator's
attention is the scarce thing here, and a question they did not need to be asked
spends it.

Do not raise the same question twice. Check `open-questions.md` first; if it is
already there, it is already open, and asking again teaches the Operator that
these can be ignored.

## What makes a question admissible

One test decides it: **someone with the application open and no code checked out
can answer it.** If answering would require reading the source, the question is
aimed at the wrong person and is not yet a question — it is work the Migration
has not finished doing.

That test is not a style preference. The Operator knows Testsigma and the
application under test, and does not necessarily read code. A question they have
to decode before they can answer is one they will defer, and a deferred question
is the failure this whole apparatus exists to prevent.

Phrase it in Testsigma's terms and the application's terms. "When the order
confirmation appears, does the reference number ever change between runs?" is
answerable. "Does `OrderPage.getRef()` return a stable value?" is not.

## What a question may never contain

Never put any of these in front of the Operator:

- **code** — a snippet, a method name, a class name, a selector
- **a file path** — including a bare filename
- **a stack trace** — or any fragment of one
- **a diagnostic code** — the CLI's or anyone else's

Each is a thing they would have to decode before they could answer, and decoding
it is the one thing they cannot do. A question carrying one is not a hard
question; it is a question put to the wrong person.

The rule is where the detail goes, not that it is destroyed. Every one of these
is a fact the Migration needs, and it goes into the Migration Directory — the
diagnostic code into `check-record.md`, the source detail into the Step Map row
or `residue.md` it belongs to. Strip it from the question and record it there, so
that the answer can be attached to it later.

## Offering answers

Never ask an open question. Every question offers a short list of the answers
that are actually possible, so the Operator is choosing rather than composing.
Three or four options is usually the whole space; if it genuinely is not, the
question is too large and should be split.

Mark one as recommended, and say why in a sentence. The reason is what makes the
recommendation checkable: an Operator who can see the grounds can overrule them,
and one who cannot is having the decision taken for them while appearing to make
it. Recommend the option that is safest to be wrong about, which is not always
the most likely one.

Include what happens if they pick each, where the consequences differ. An option
whose cost is invisible is not really on the list.

## Recording it, and what clears it

Write the question into `open-questions.md` at the moment it is raised, before
putting it to the Operator and before doing anything that depends on the answer.
A question that exists only in the session's transcript is lost when the session
ends, and the session always ends.

Only an answer clears a question. Nothing else does — not the Phase moving on,
not the question becoming awkward, not a later session deciding it looks stale,
and not the work having proceeded on a guess in the meantime. If the work went
ahead on an assumption, the question stays open and the assumption is recorded
beside it, because that is precisely the case where a wrong answer is expensive.

An unanswered question survives every session boundary. `resume` reads this file
at the start of every session and surfaces each one in full, which is what makes
"still open" mean something.

This is designed against a failure that has already happened rather than an
imagined one. The one structured question ever put to an Operator in the
conversion that produced this plugin was never answered, and nothing in the
system recorded that it was still waiting. It was not refused; it was simply
lost.

## Platform Facts and Application Facts

What the Migration learns is kept in two files, and which file a thing goes in is
decided by **who can answer it** — the only distinction that changes what you do
next.

A **Platform Fact** is something true of Testsigma's own authoring surface that no
reading of a source could reveal. The Migration settles one by probing rather
than by raising a question, and records it in `platform-facts.md` with how it was
established. Probing is repeatable and an Operator's recollection is not, so even
where they would know, the probe is the better answer.

An **Application Fact** is something true of the application under test. Only a
person who knows that application can answer one, so it goes into
`application-facts.md` and stays open until answered — the same discipline as an
open question, in a separate file because the two get answered by different
means.

When you cannot tell which kind you have, ask whether probing could settle it. If
it could, it is a Platform Fact and you have not finished probing. If it could
not, it is an Application Fact and it is time to ask.

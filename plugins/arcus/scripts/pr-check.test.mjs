import assert from "node:assert/strict";
import { test } from "node:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { COMMENT_MARKER, diff, judgePacket, report, storyOf, storyTests, testsOf, verdictOf, writePackets } from "./pr-check.mjs";

const run = (p, status, failedStep) => ({
  run: {
    path: p,
    title: p.replace(/^.*\//, "").replace(".sigma", ""),
    status,
    durationMs: 10,
    artifactsDir: "/runs/x",
    ...(failedStep && { failedStep: { description: failedStep, message: "not visible", screenshot: "step-3.jpg" } }),
  },
});
const suite = (...tests) => ({ suite: { status: "failed", tests } });
const steps = () => 'nav "{env.base_url}/x"';

const ISSUE = {
  issue: { id: "wi-1", key: "K-1", title: "Discount code" },
  acceptanceCriteria: ["A valid code lowers the total", "An expired code is refused"],
  cases: [
    { id: "c1", label: "K-TC-1", title: "Apply a valid code", file: "g/tests/a.sigma", review: "ACCEPTED" },
    { id: "c2", label: "Refuse an expired code", title: "Refuse an expired code", file: null, review: "PENDING" },
  ],
};

test("the story's tests are the files issue show names for its cases", () => {
  assert.deepEqual(storyTests(ISSUE), [{ path: "g/tests/a.sigma", case_id: "c1" }]);
  assert.deepEqual(storyTests(null), []);
});

test("the judge reads the issue's title and acceptance criteria as the story", () => {
  const { story, cases } = storyOf(ISSUE);
  assert.deepEqual(story, {
    issue_key: "K-1",
    title: "Discount code",
    description: "- A valid code lowers the total\n- An expired code is refused",
  });
  assert.deepEqual(cases.map((c) => c.id), ["c1", "c2"]);
  assert.deepEqual(storyOf(null), { story: null, cases: [] });
});

test("a single run and a suite read the same", () => {
  assert.equal(testsOf(run("a", "passed")).length, 1);
  assert.equal(testsOf(suite(run("a", "passed"), run("b", "failed"))).length, 2);
});

test("only a failure on the PR that passes on the base and fails again is a difference", () => {
  const out = diff({
    lane: "regression",
    pr: suite(run("t/broke.sigma", "failed", "verify @list"), run("t/ok.sigma", "passed"), run("t/flaky.sigma", "failed", "x"), run("t/old.sigma", "failed", "y")),
    base: suite(run("t/broke.sigma", "passed"), run("t/ok.sigma", "passed"), run("t/flaky.sigma", "passed"), run("t/old.sigma", "failed", "y")),
    retry: suite(run("t/broke.sigma", "failed", "verify @list"), run("t/flaky.sigma", "passed")),
    caseIds: new Map([["t/broke.sigma", "c1"]]),
    readSteps: steps,
  });
  assert.deepEqual(out.differences.map((d) => d.title), ["broke"]);
  const [d] = out.differences;
  assert.equal(d.case_id, "c1");
  assert.equal(d.pr.failed_step, "verify @list");
  assert.equal(d.pr.screenshot, "/runs/x/step-3.jpg");
  assert.equal(d.base.status, "passed");
  assert.equal(d.pr_retry.status, "failed");
  assert.deepEqual(out.passed, ["ok"]);
  assert.deepEqual(out.not_counted, ["flaky: flaky, passed when re-run on this PR", "old: fails the same way on the base, so not this PR's"]);
});

test("a test that fails on both builds, but in another way on the PR, is a difference", () => {
  const prFail = { ...run("t/tabs.sigma", "failed", "verify url ~ tab=connection") };
  const baseFail = run("t/tabs.sigma", "failed", "verify url ~ tab=connection");
  baseFail.run.failedStep.message = "toast check: element not found";
  const out = diff({ lane: "regression", pr: suite(prFail), base: suite(baseFail), retry: suite(prFail), readSteps: steps });
  assert.deepEqual(out.differences.map((d) => d.title), ["tabs"]);
  assert.equal(out.differences[0].base.message, "toast check: element not found");
});

test("an absolute screenshot path is kept as it is", () => {
  const t = run("t/a.sigma", "failed", "x");
  t.run.failedStep.screenshot = "/abs/run/step.jpg";
  const out = diff({ lane: "break", pr: suite(t), base: suite(run("t/a.sigma", "passed")), readSteps: steps });
  assert.equal(out.differences[0].pr.screenshot, "/abs/run/step.jpg");
});

test("a test that did not compile, or never ran on the base, is said, not judged", () => {
  const out = diff({
    lane: "break",
    pr: suite(run("t/bad.sigma", "refused"), run("t/half.sigma", "failed", "x")),
    base: suite(),
    readSteps: steps,
  });
  assert.equal(out.differences.length, 0);
  assert.deepEqual(out.not_counted, ["bad: did not compile, so it did not run", "half: not run on the base"]);
});

const difference = (lane, title, extra = {}) => ({
  lane,
  title,
  steps: 'verify @list contains "v2"',
  case_id: lane === "regression" ? "c1" : "",
  pr: { status: "failed", failed_step: "verify @list", message: "not visible", screenshot: "" },
  base: { status: "passed", failed_step: "", message: "", screenshot: "" },
  pr_retry: { status: "failed", failed_step: "verify @list", message: "not visible", screenshot: "" },
  ...extra,
});

test("the judge's packet holds the story, the cases, the test and each side, and only screenshots that exist", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pr-check-"));
  const shot = path.join(dir, "step.jpg");
  fs.writeFileSync(shot, "JPEG");
  const d = difference("break", "Search by name", { pr: { status: "failed", failed_step: "verify @list", message: "", screenshot: shot }, base: { status: "passed", screenshot: path.join(dir, "gone.jpg") } });
  const text = judgePacket(storyOf(ISSUE), d);
  assert.match(text, /K-1: Discount code\n- A valid code lowers the total/);
  assert.match(text, /- Apply a valid code/);
  assert.match(text, /a test written to break the change/);
  assert.match(text, /PR build, re-run: failed/);
  assert.ok(text.includes(`- PR build: ${shot}`));
  assert.ok(!text.includes("gone.jpg"));
  fs.rmSync(dir, { recursive: true });
});

test("packets are numbered in the order the report reads the verdicts", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pr-check-"));
  const diffs = [
    { lane: "regression", differences: [difference("regression", "a")], passed: [], not_counted: [] },
    { lane: "break", differences: [difference("break", "b")], passed: [], not_counted: [] },
  ];
  const out = writePackets({ issue: null, diffs, out: dir });
  assert.deepEqual(out.map((p) => [p.n, p.title]), [[1, "a"], [2, "b"]]);
  assert.match(fs.readFileSync(out[0].packet, "utf8"), /No story is linked/);
  fs.rmSync(dir, { recursive: true });
});

test("an unreadable verdict is ambiguous, and a low-confidence bug in the break lane is unclear", () => {
  assert.equal(verdictOf("regression", { verdict: "nonsense", confidence: 4 }).verdict, "ambiguous");
  assert.equal(verdictOf("regression", undefined).verdict, "ambiguous");
  assert.equal(verdictOf("break", { verdict: "real_bug", confidence: 2, reason: "r" }).verdict, "ambiguous");
  assert.equal(verdictOf("regression", { verdict: "real_bug", confidence: 2, reason: "r" }).verdict, "real_bug");
});

test("a story case that is a real bug blocks; a break finding never does", () => {
  const diffs = [
    { lane: "regression", differences: [difference("regression", "Profiles show version")], passed: ["Search by name"], not_counted: [] },
    { lane: "break", differences: [difference("break", "Rename twice")], passed: [], not_counted: ["c: flaky"] },
  ];
  const out = report({
    issue: ISSUE,
    prUrl: "http://pr",
    baseUrl: "http://base",
    diffs,
    verdicts: [
      { verdict: "real_bug", confidence: 4, reason: "Version shows v1." },
      { verdict: "real_bug", confidence: 5, reason: "The second rename is lost." },
    ],
    stats: { scenarios_run: 3, minutes: 12.6, budget: "low" },
  });
  assert.equal(out.conclusion, "failure");
  assert.deepEqual(out.findings.map((f) => f.blocks), [true, false]);
  assert.ok(out.comment.startsWith(COMMENT_MARKER));
  assert.match(out.comment, /Blocks the merge:\*\* 1 of the story's cases/);
  assert.match(out.comment, /3 scenarios, 1 findings/);
  assert.match(out.comment, /in 13 min\. Budget low/);
  assert.match(out.comment, /### Passed on both builds\n\n- Search by name/);
  assert.match(out.comment, /### Not run\n\n- c: flaky/);
});

test("an intended change does not block and asks for the case to be updated", () => {
  const diffs = [{ lane: "regression", differences: [difference("regression", "a")], passed: [], not_counted: [] }];
  const out = report({ issue: ISSUE, prUrl: "p", baseUrl: "b", diffs, verdicts: [{ verdict: "intended_change", confidence: 4, reason: "The story asks for it." }] });
  assert.equal(out.conclusion, "success");
  assert.match(out.comment, /Update the case in QI/);
});

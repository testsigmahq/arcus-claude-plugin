#!/usr/bin/env node
// The deterministic half of /arcus:pr-check: which tests are the story's, running them on each build, and
// keeping only what fails on the PR's build, passes on the base build, and fails again on a retry, then the judge's
// packets and the one PR comment its verdicts make.
// Node 22+, no dependencies. Every command writes JSON to stdout.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const USAGE = `usage:
  pr-check.mjs story-tests --issue <issue.json>
  pr-check.mjs run --url <url> [--project <name>] [--var name=value ...] <paths...>
  pr-check.mjs diff --lane regression|break --pr <run.json> --base <run.json> [--retry <run.json>] [--issue <issue.json>]
  pr-check.mjs packets [--issue <issue.json>] --out <dir> [--diff <diff.json> ...]
  pr-check.mjs report [--issue <issue.json>] --pr-url <url> --base-url <url> [--diff <diff.json> ...]
                      [--verdicts <verdicts.json>] [--decisions <decisions.json>] [--stats <stats.json>]
                      [--local] [--comment <comment.md>]
  pr-check.mjs splice --section <comment.md> [--into <body.md>]`;

function parse(argv) {
  const opts = { _: [], var: [], diff: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) {
      opts._.push(a);
      continue;
    }
    const key = a.slice(2);
    if (key === "local") {
      opts[key] = true;
      continue;
    }
    const value = argv[++i];
    if (value === undefined) fail(`--${key} needs a value`);
    if (Array.isArray(opts[key])) opts[key].push(value);
    else opts[key] = value;
  }
  return opts;
}

function fail(message) {
  process.stderr.write(`${message}\n${USAGE}\n`);
  process.exit(2);
}

const readJson = (file) => JSON.parse(fs.readFileSync(file, "utf8"));

/**
 * The test files `arcus issue show --json` names for the story's cases, with each file's case. A case can name a file
 * this checkout does not have (pushed from another branch, or by an earlier check that then deleted it): it is not run.
 */
export function storyTests(issue, exists = fs.existsSync) {
  return (issue?.cases ?? []).filter((c) => c.file && exists(c.file)).map((c) => ({ path: c.file, case_id: c.id }));
}

/** The story the judge reads, from `arcus issue show --json`: its key, title and acceptance criteria. */
export function storyOf(issue) {
  if (!issue?.issue) return { story: null, cases: [] };
  return {
    story: {
      issue_key: issue.issue.key,
      title: issue.issue.title ?? "",
      description: (issue.acceptanceCriteria ?? []).map((c) => `- ${c}`).join("\n"),
    },
    cases: (issue.cases ?? []).map((c) => ({ id: c.id, title: c.title ?? c.label ?? "", acceptance_status: c.review ?? "" })),
  };
}

/** One `arcus test run --json` answer, single test or suite, as a list of test runs. */
export function testsOf(runJson) {
  if (runJson.suite) return runJson.suite.tests;
  if (runJson.run) return [runJson];
  return [];
}

function outcome(test) {
  if (!test) return null;
  const { run } = test;
  const failed = run.failedStep;
  return {
    status: run.status,
    failed_step: failed?.description ?? run.interruptedAt ?? "",
    message: failed?.message ?? run.problem ?? "",
    screenshot: !failed?.screenshot
      ? ""
      : path.isAbsolute(failed.screenshot) || !run.artifactsDir
        ? failed.screenshot
        : path.join(run.artifactsDir, failed.screenshot),
  };
}

const failureOf = (test) => [test.run.failedStep?.description ?? "", test.run.failedStep?.message ?? test.run.problem ?? ""];

function sameFailure(a, b) {
  const [stepA, messageA] = failureOf(a);
  const [stepB, messageB] = failureOf(b);
  return stepA === stepB && messageA === messageB;
}

const byPath = (runJson) => new Map(testsOf(runJson).map((t) => [t.run.path, t]));

/**
 * Splits the tests into what goes to the judge and what does not.
 * A difference fails on the PR and fails again on the retry, while the base passes or fails in another way (another
 * step, or another message). A test that passes on the retry is flaky; one that fails the same way on the base was
 * already broken. Neither is this PR's.
 */
export function diff({ lane, pr, base, retry, caseIds = new Map(), readSteps = (p) => fs.readFileSync(p, "utf8") }) {
  const prs = byPath(pr);
  const bases = byPath(base);
  const retries = retry ? byPath(retry) : new Map();
  const out = { lane, differences: [], passed: [], not_counted: [] };
  for (const [p, t] of prs) {
    const b = bases.get(p);
    const title = t.run.title || path.basename(p, ".sigma");
    if (t.run.status === "passed") {
      if (b?.run.status === "passed") out.passed.push(title);
      else out.not_counted.push(`${title}: passed on this PR, ${b ? `${b.run.status} on the base` : "not run on the base"}`);
      continue;
    }
    if (t.run.status === "refused") {
      out.not_counted.push(`${title}: did not compile, so it did not run`);
      continue;
    }
    if (!b) {
      out.not_counted.push(`${title}: not run on the base`);
      continue;
    }
    if (b.run.status !== "passed" && sameFailure(t, b)) {
      out.not_counted.push(`${title}: fails the same way on the base, so not this PR's`);
      continue;
    }
    const r = retries.get(p);
    if (r?.run.status === "passed") {
      out.not_counted.push(`${title}: flaky, passed when re-run on this PR`);
      continue;
    }
    out.differences.push({
      lane,
      title,
      steps: readSteps(p),
      case_id: caseIds.get(p) ?? "",
      pr: outcome(t),
      base: outcome(b),
      pr_retry: outcome(r),
    });
  }
  return out;
}

const differencesOf = (diffs) => diffs.flatMap((d) => d.differences);

function side(name, o) {
  if (!o) return `${name}: not run`;
  const parts = [`${name}: ${o.status}`];
  if (o.failed_step) parts.push(`failed at: ${o.failed_step}`);
  if (o.message) parts.push(`message: ${o.message}`);
  return parts.join("\n  ");
}

const SIDES = [
  ["PR build", "pr"],
  ["Base build", "base"],
  ["PR build, re-run", "pr_retry"],
];

/** What the judge reads for one difference: the story, its cases, the test and what each build did. Never the diff. */
export function judgePacket({ story, cases }, difference) {
  const storyText = story ? `${story.issue_key}: ${story.title}\n${story.description}`.trim() : "No story is linked to this PR.";
  const caseLines = cases.map((c) => `- ${c.title}`).join("\n") || "- none";
  const kind = difference.lane === "regression" ? "one of the story's own test cases" : "a test written to break the change";
  const shots = SIDES.filter(([, k]) => difference[k]?.screenshot && fs.existsSync(difference[k].screenshot)).map(
    ([name, k]) => `- ${name}: ${difference[k].screenshot}`,
  );
  return [
    `## Story\n${storyText}`,
    `## The story's test cases\n${caseLines}`,
    `## The test (${kind})\n${difference.title}\n\n${difference.steps}`,
    `## What happened\n${SIDES.map(([name, k]) => side(name, difference[k])).join("\n")}`,
    `## Screenshots at the failing step\n${shots.join("\n") || "- none"}`,
  ].join("\n\n");
}

/** One packet file per difference, numbered in the order the report reads the verdicts. */
export function writePackets({ issue, diffs, out }) {
  const context = storyOf(issue);
  fs.mkdirSync(out, { recursive: true });
  return differencesOf(diffs).map((d, i) => {
    const packet = path.join(out, `judge-${i + 1}.md`);
    fs.writeFileSync(packet, `${judgePacket(context, d)}\n`);
    return { n: i + 1, lane: d.lane, title: d.title, packet };
  });
}

export const COMMENT_MARKER = "<!-- arcus-pr-check:v1 -->";
export const SECTION_END = "<!-- /arcus-pr-check -->";
export const RAN_LOCALLY_MARKER = "<!-- arcus:ran-locally -->";
const VERDICTS = ["real_bug", "intended_change", "test_issue", "environment_issue", "ambiguous"];
const LABELS = {
  real_bug: "Likely bug",
  intended_change: "Intended change",
  test_issue: "Test issue",
  environment_issue: "Environment issue",
  ambiguous: "Unclear",
};
const REPORTED = new Set(["real_bug", "ambiguous"]);
// While the break lane is advisory, a low-confidence bug there is reported as unclear rather than as a bug.
const ADVISORY_MIN_CONFIDENCE = 3;

/** A verdict as the judge gave it, or ambiguous when it gave none that reads. */
export function verdictOf(lane, given) {
  const v =
    given && VERDICTS.includes(given.verdict) && Number.isInteger(given.confidence) && given.confidence >= 1 && given.confidence <= 5
      ? { verdict: given.verdict, confidence: given.confidence, reason: String(given.reason ?? "").trim() }
      : { verdict: "ambiguous", confidence: 1, reason: "The judge gave no verdict that reads." };
  if (lane === "break" && v.verdict === "real_bug" && v.confidence < ADVISORY_MIN_CONFIDENCE) return { ...v, verdict: "ambiguous" };
  return v;
}

function outcomeMd(o) {
  if (!o) return "not run";
  let text = o.status;
  if (o.failed_step) text += ` at \`${o.failed_step}\``;
  if (o.message) text += `: ${o.message}`;
  if (o.screenshot) text += ` (screenshot \`${path.basename(o.screenshot)}\` in the run's artifacts)`;
  return text;
}

function decisionMd(decision) {
  if (!decision) return [];
  if (decision.choice === "fixed") return ["- **Developer:** fixed, and it passes on a re-run on this change."];
  return [`- **Developer:** shipping it: ${decision.reason}`];
}

function findingMd({ difference: d, verdict: v, decision }) {
  const lines = [
    `#### ${LABELS[v.verdict]}: ${d.title}`,
    `${v.reason} (confidence ${v.confidence}/5)`,
    "",
    `- **This PR:** ${outcomeMd(d.pr)}`,
    `- **Re-run on this PR:** ${outcomeMd(d.pr_retry)}`,
    `- **Base:** ${outcomeMd(d.base)}`,
  ];
  if (v.verdict === "intended_change" && d.case_id) lines.push("- **Next:** the story asks for this. Update the case in QI; it waits there as pending.");
  lines.push(...decisionMd(decision));
  lines.push("", "<details><summary>Steps to reproduce</summary>", "", "```", d.steps, "```", "", "</details>");
  return lines.join("\n");
}

/**
 * Verdicts into findings, what blocks, and the one PR comment. `verdicts` is in packet order: `verdicts[i]` judges
 * packet `i + 1`. Only the story's own cases block, and not when the story asked for the new behaviour.
 */
export function report({ issue, prUrl, baseUrl, diffs, verdicts = [], decisions = [], stats = {}, local = false }) {
  const { story } = storyOf(issue);
  const decided = new Map(decisions.map((d) => [d.n, d]));
  const findings = differencesOf(diffs).map((difference, i) => {
    const verdict = verdictOf(difference.lane, verdicts[i]);
    const decision = decisionOf(decided.get(i + 1));
    const broken = difference.lane === "regression" && REPORTED.has(verdict.verdict);
    return { difference, verdict, decision, blocks: broken && decision?.choice !== "fixed" };
  });
  const passed = diffs.filter((d) => d.lane === "regression").flatMap((d) => d.passed);
  const notRun = diffs.flatMap((d) => d.not_counted);
  const blocking = findings.filter((f) => f.blocks);
  const fixedCases = findings.filter((f) => f.difference.lane === "regression" && f.decision?.choice === "fixed");
  const reported = findings.filter((f) => f.difference.lane === "break" && REPORTED.has(f.verdict.verdict));
  const other = findings.filter((f) => !blocking.includes(f) && !fixedCases.includes(f) && !reported.includes(f));
  const open = findings.filter((f) => REPORTED.has(f.verdict.verdict) && f.decision?.choice !== "fixed");

  const conclusion = blocking.length ? "failure" : notRun.length || open.length ? "neutral" : "success";

  const storyLine = story ? `Story **${story.issue_key}**: ${story.title}` : "No story is linked to this PR, so the story's cases were not run.";
  const lane1 = blocking.length
    ? `**Blocks the merge:** ${blocking.length} of the story's cases broke on this PR.`
    : story
      ? `**The story's cases:** ${passed.length} passed on both builds, none broke.`
      : "";
  let lane2 = `**Tried to break it:** ${stats.scenarios_run ?? 0} scenarios, ${reported.length} findings (advisory, they don't block).`;
  const fixed = reported.filter((f) => f.decision?.choice === "fixed").length;
  const shipped = reported.filter((f) => f.decision?.choice === "shipped");
  if (fixed) lane2 += ` Fixed ${fixed}.`;
  if (shipped.length) lane2 += ` Shipping ${shipped.length}: ${[...new Set(shipped.map((f) => f.decision.reason))].map((r) => `"${r}"`).join("; ")}.`;
  let run = local
    ? `Ran locally by the developer, not a CI result: the change and its merge base, one after the other, at \`${prUrl}\``
    : `Tested \`${prUrl}\` against \`${baseUrl}\``;
  if (stats.minutes) run += ` in ${Math.round(stats.minutes)} min`;
  if (stats.budget) run += `. Budget ${stats.budget}`;
  if (stats.stopped_because) run += `, stopped: ${stats.stopped_because}`;
  const summary = [storyLine, lane1, lane2, `${run}.`].filter(Boolean).join("\n\n");

  const sections = [];
  if (blocking.length) sections.push("### Blocking: the story's cases", ...blocking.map(findingMd));
  if (fixedCases.length) sections.push("### Story cases fixed before review", ...fixedCases.map(findingMd));
  if (passed.length) sections.push("### Passed on both builds", passed.map((t) => `- ${t}`).join("\n"));
  if (reported.length) sections.push("### Findings from trying to break it", ...reported.map(findingMd));
  if (other.length) sections.push("### Not counted", ...other.map(findingMd));
  if (notRun.length) sections.push("### Not run", notRun.map((line) => `- ${line}`).join("\n"));

  const title = local ? "### Checked against the base build, and tried to break it" : "## Arcus PR check";
  const comment = [COMMENT_MARKER, title, summary, ...sections, ...(local ? [SECTION_END] : [])].join("\n\n");
  return { conclusion, findings, comment };
}

/** The developer's choice for one finding, when it reads: fixed, or shipped with a one-line reason. */
export function decisionOf(given) {
  if (given?.choice === "fixed") return { choice: "fixed" };
  if (given?.choice === "shipped" && String(given.reason ?? "").trim()) return { choice: "shipped", reason: String(given.reason).trim() };
  return null;
}

/**
 * The PR comment with the check's section in it. With a "Ran locally" comment on the PR, the section replaces
 * an earlier one, or goes at the end. Without one, the section is the whole comment.
 */
export function splice(body, section) {
  if (!body || !body.startsWith(RAN_LOCALLY_MARKER)) return section;
  const start = body.indexOf(COMMENT_MARKER);
  if (start === -1) return `${body.trimEnd()}\n\n${section}`;
  const end = body.indexOf(SECTION_END, start);
  const rest = end === -1 ? "" : body.slice(end + SECTION_END.length);
  return `${body.slice(0, start).trimEnd()}\n\n${section}${rest}`;
}

/** One file's run, as `arcus test run --json` answers it. The released CLI takes one test file per run. */
function runOne(file, opts) {
  const args = ["test", "run", file, "--json", "--screenshots", "failed", "--base-url", opts.url];
  if (opts.project) args.push("--project", opts.project);
  for (const v of opts.var) args.push("--var", v);
  try {
    return JSON.parse(execFileSync("arcus", args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024, stdio: ["ignore", "pipe", "inherit"] }));
  } catch (e) {
    // A failed test exits 1 with its result on stdout. With nothing there, the run never started. The error's own
    // message holds the command line, and with it any --var value, so it is never printed.
    if (e.stdout) return JSON.parse(e.stdout);
    return { run: { path: file, title: path.basename(file, ".sigma"), status: "refused", problem: `arcus test run did not start (exit ${e.status ?? "unknown"})` } };
  }
}

/** Several runs as one suite, the shape `diff` reads. */
export function suiteOf(runs) {
  return { suite: { tests: runs.flatMap(testsOf) } };
}

function main(argv) {
  const [command, ...rest] = argv;
  const opts = parse(rest);
  switch (command) {
    case "story-tests":
      if (!opts.issue) fail("story-tests needs --issue");
      return storyTests(readJson(opts.issue));
    case "run":
      if (!opts.url || opts._.length === 0) fail("run needs --url and at least one path");
      return suiteOf(opts._.map((file) => runOne(file, opts)));
    case "diff": {
      if (!["regression", "break"].includes(opts.lane) || !opts.pr || !opts.base) fail("diff needs --lane, --pr and --base");
      const caseIds = new Map(opts.issue ? storyTests(readJson(opts.issue)).map((t) => [t.path, t.case_id]) : []);
      return diff({
        lane: opts.lane,
        pr: readJson(opts.pr),
        base: readJson(opts.base),
        retry: opts.retry ? readJson(opts.retry) : null,
        caseIds: opts.lane === "regression" ? caseIds : new Map(),
      });
    }
    case "packets":
      if (!opts.out) fail("packets needs --out");
      return writePackets({ issue: opts.issue ? readJson(opts.issue) : null, diffs: opts.diff.map(readJson), out: opts.out });
    case "report": {
      if (!opts["pr-url"] || !opts["base-url"]) fail("report needs --pr-url and --base-url");
      const out = report({
        issue: opts.issue ? readJson(opts.issue) : null,
        prUrl: opts["pr-url"],
        baseUrl: opts["base-url"],
        diffs: opts.diff.map(readJson),
        verdicts: opts.verdicts ? readJson(opts.verdicts) : [],
        decisions: opts.decisions ? readJson(opts.decisions) : [],
        stats: opts.stats ? readJson(opts.stats) : {},
        local: Boolean(opts.local),
      });
      if (opts.comment) fs.writeFileSync(opts.comment, `${out.comment}\n`);
      return out;
    }
    case "splice": {
      if (!opts.section) fail("splice needs --section");
      const body = opts.into && fs.existsSync(opts.into) ? fs.readFileSync(opts.into, "utf8") : "";
      return { body: splice(body, fs.readFileSync(opts.section, "utf8").trimEnd()) };
    }
    default:
      fail(command ? `unknown command ${command}` : "no command");
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  process.stdout.write(`${JSON.stringify(main(process.argv.slice(2)), null, 2)}\n`);
}

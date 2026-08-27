# IND HIVE — Module 1 POC web demo

A single Cloudflare Worker that serves the demo site and an assistant backed by
`claude-opus-5`. The assistant does not author regulatory content: it calls the
deterministic Module 1 pipeline as tools and explains what came back.

```
Python POC pipeline  ──build──▶  src/cases.json  ──▶  Worker  ──▶  browser
(source of truth)                 (build artifact)     │
                                                       ├─ deterministic tools
                                                       ├─ cover letter drafting (Opus 5)
                                                       └─ grounding check
```

## Why the pipeline output is pre-built

The Form 1571 mapping, the Module 1 TOC, and the validation checks are
deterministic — same input, same output, always. Running them at request time
and shipping their output as a build artifact produce byte-identical results, so
the Worker ships the artifact and stays a single deploy unit with no second host.

The Python code in `../indkit/` remains the only implementation of that
logic. Nothing is reimplemented in TypeScript.

Regenerate the bundle whenever the pipeline or the source cases change:

```bash
cd ../indkit && python scripts/run_pipeline.py --all
cd ../V1 && python build/bundle_cases.py
```

## Setup

```bash
npm install
```

Then create `.dev.vars` (git-ignored) with your Anthropic key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Run locally

```bash
npm run dev
```

`wrangler dev` runs the real Workers runtime, so local behaviour matches
production. Open http://127.0.0.1:8787.

## Deploy

```bash
npx wrangler secret put ANTHROPIC_API_KEY
npm run deploy
```

Then attach `indhive.com` to the Worker as a custom domain in the Cloudflare
dashboard, or add a `routes` entry to `wrangler.jsonc`.

## Layout

```
build/bundle_cases.py   collects pipeline output into src/cases.json
src/index.ts            Worker: routes, chat loop, SSE, tool dispatch
src/tools.ts            tool definitions + deterministic handlers
src/grounding.ts        text-level check on generated prose
src/prompt.ts           system prompt + cover letter prompt
public/index.html       shell: top bar, hero, case rail, module grid, detail, chat panel
public/styles.css       brand tokens and layout
public/app.js           navigation, artifact renderers, chat client
public/favicon.svg      hive mark
```

## Six views per case

One **Input** view showing the source records the pipeline was given, with each field
labelled by the output it reached, and five **generated output** views. Input and
output are separated on the home page so the direction of flow is unambiguous.

Form 1571 follows the real form: boxes 1-12 and 14 carry only fields that exist on
that form, Box 9 resolves to `None`, and Box 12 renders as the real Contents of
Application checklist, ticked from what the package actually contains. Values the
pipeline carries for other documents but which do not appear on Form 1571 (dosage
form, route, protocol identifiers, investigator contact details) are grouped
separately and labelled as such.

## The two things this demo is built to prove

**Traceability.** Every Form 1571 value carries the source record it came from.
Clicking a field lights up that record in the side rail.

**Refusal.** When source records disagree (IND003, IND009), the pipeline leaves
the canonical value empty and records a conflict. The assistant is instructed to
present every competing value and never choose between them, including when
asked directly.

## Grounding check

`draft_cover_letter` is the only path where a model writes prose. It receives an
approved fact whitelist and nothing else. The returned text is then scanned for
emails, phone numbers, dates, and postal codes that do not trace back to that
whitelist, and anything unaccounted for is surfaced above the letter.

Omitting an approved fact is allowed. Stating something that is not an approved
fact is flagged.

## Limits

- Ten fixed synthetic cases. No user-supplied cases yet.
- Source records are already extracted. Reading them out of real PDF, DOCX or
  spreadsheet documents is not built; the input view says so at the top.
- Investigator contact details are carried but unused - they belong on Form FDA 1572,
  which has no generator.
- Section 1.20 is supplied for four cases only (IND001, IND004, IND005 complete;
  IND006 deliberately incomplete). The rest exercise the ABSENT path.
- No login. Anyone with the link can use the assistant.
- Rate limiting is a best-effort in-isolate counter. Add a Cloudflare
  rate-limiting rule on `/api/chat` before sharing the link widely.
- No conversation persistence; a refresh clears the thread.
- The Module 1 TOC resolves against the US regional M1 section structure, but
  applicability is a demonstration heuristic for Initial INDs, not regulatory
  advice.
- The cover letter has no FDA division addressee, because no source record
  supplies one. That is correct refusal behaviour, not a rendering bug.
- All case data is fictional. Nothing here is submittable to FDA.

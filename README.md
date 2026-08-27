# INDHIVE

**Live at [indhive.com](https://indhive.com)** · fallback [indhive.pumpkin-ai-v2.workers.dev](https://indhive.pumpkin-ai-v2.workers.dev)

A demonstration of automated FDA IND **Module 1** preparation.

Synthetic sponsor, product, protocol and plan records go in. A deterministic pipeline
normalises them into one canonical record and maps that into Module 1 artifacts. Every
value keeps the source record it came from. Where two records disagree, the value is left
empty and flagged — the system does not choose.

One case is different. A clinical partner built a real-shaped input package for a
programme of his own — PMX-103 — and sent his own answers with it: a hand-filled Form 1571,
a ten-entry gaps log, a traceability matrix declaring 23 numbers that must agree across his
dossiers. The pipeline ran on his input and never saw his answers. Four comparison views
then put the two side by side.

**Nothing here is submittable to FDA.** Every case is fictional, including PMX-103, and this
is a proof of concept, not regulatory software.

---

## Two halves

```
inputs/partner-package/    the partner's PMX-103 package — git-ignored, 21 CFR 312.130
        │
        │  python build/extract_partner_package.py   map it into a case + an answer key
        │  python scripts/scan_invariants.py           check his 23 numbers across the corpus
        ▼
indkit/                 the Python project — the only implementation of the logic
        │
        │  python scripts/run_pipeline.py --all        generate artifacts for all 11 cases
        │  python build/bundle_cases.py   collect them into V1/src/cases.json
        ▼
V1/                     the web app — a Cloudflare Worker serving the showcase
```

The Form 1571 mapping, the Module 1 gap analysis, the 1.20 plan assembly and the validation
rules live in Python and nowhere else. The Worker ships their output as a build artifact and
adds the two things that must run live: cover letter drafting, and the grounding check that
verifies the draft against the approved facts.

Those pipeline steps are deterministic, so precomputing them and running them per request
produce byte-identical results.

## What each case shows

Six views. One **Input** — the source records supplied, with each field labelled by the
output it reached — and five generated outputs:

| View | What it is |
|---|---|
| Form FDA 1571 | Boxes 1–12 and 14, real box numbers, per-field status and source |
| Cover letter | Drafted from an approved fact whitelist, then checked for unsupported claims |
| 1.20 General Investigational Plan | The six elements required by 21 CFR 312.23(a)(3)(iv) |
| Module 1 gap analysis | The US regional M1 skeleton resolved into PRESENT / ABSENT / NEEDS DECISION / N/A |
| Validation | Field presence, source conflicts, cross-document consistency |

Ten fictional cases: six clean, two with missing data (IND002, IND008), two with conflicting
sources (IND003, IND009), one with unusual formatting (IND010). Section 1.20 is supplied for
four cases only, so the gap analysis differs case to case.

### PMX103, the partner case

Four more views, and they exist only where somebody supplied answers to check against:

| View | What it is |
|---|---|
| Gap crosswalk | Our derived gap list beside his GAPS Log, matched on topic. Four of his ten came back independently |
| 1571 vs his draft | Box by box against the 1571 he filled by hand, organised by the numbers printed on the real form |
| Invariant scan | His 23 declared numbers, located deterministically, adjudicated sentence by sentence, compared in code |
| Package review | Cross-document checks over his own material: section numbering, module assignment, file references |

Module 1 consumes about 35 scalar fields from his package and deliberately leaves the rest —
dose levels, toxicology, CMC specifications, PK — to Modules 3 to 5, which are not built.
The site says so on the page rather than waiting to be asked.

An assistant backed by `claude-opus-5` acts as the guide. It never states a case fact that
did not come from a tool call, never resolves a conflict, and never claims filing readiness.

## Run it

```bash
cd V1
npm install
```

Create `V1/.dev.vars` (git-ignored):

```
ANTHROPIC_API_KEY=sk-ant-...
```

```bash
npm run dev          # http://127.0.0.1:8787
```

`wrangler dev` runs the real Workers runtime, so local behaviour matches production.

To regenerate everything from the pipeline:

```bash
cd indkit && python scripts/run_pipeline.py --all
cd ../V1 && python build/bundle_cases.py
```

### Rebuilding the partner case

Only needed when the PMX-103 package changes. Its documents are not in version control, so
these steps are the reason the committed JSON exists at all.

```bash
cd indkit && pip install -r requirements-build.txt
python build/extract_partner_package.py
```

That writes `data/source_cases/PMX103.json` (the case the pipeline runs) and
`data/partner_reference/PMX103.json` (his answers, never an input to generation).

The invariant scan is separate: it reads 720k characters of dossier and calls a model, so it
runs on demand rather than on every rebuild.

```bash
python scripts/scan_invariants.py
```

A report where all 23 read the same is the right answer and a poor demonstration. To make
the scan fail on purpose, on a throwaway copy of the package:

```bash
python build/tamper_demo.py --show
```

> On Windows, `Ctrl+C` does not always stop `workerd`. If a change appears not to take
> effect, kill the strays before restarting:
> ```powershell
> Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'workerd.exe' -or ($_.Name -in @('node.exe','cmd.exe') -and $_.CommandLine -match 'wrangler') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
> ```

## Deploy

```bash
cd V1
npx wrangler deploy
```

Both hostnames are already declared as custom domains in `wrangler.jsonc`, so wrangler
maintains their DNS records and certificates. The Anthropic key is already set as a Worker
secret; it only needs re-running (`npx wrangler secret put ANTHROPIC_API_KEY`) if the key
is rotated.

`/api/chat` is rate limited at the edge by the `CHAT_LIMIT` binding declared in
`wrangler.jsonc` (8 requests / 60s per IP), backed by an in-isolate burst counter. Edge
limits are eventually consistent, so treat them as a backstop against sustained abuse
rather than an exact gate. The endpoint is unauthenticated by design.

Full deployment procedure, verification checklist and rollback points: [DEPLOY.md](DEPLOY.md).

## Not built

- **Extraction from real documents.** Source records arrive already structured. A general
  layer that reads arbitrary PDF, DOCX or spreadsheets is the largest missing piece. PMX103
  is not an exception: a build script written against those specific files pulled its records
  out once, and the result was committed. Nothing reads a document at run time.
- Form FDA 1572, Form FDA 3674, investigational drug labeling — no generators.
- eCTD packaging, Part 11 signatures, audit trail.
- Modules 2, 3, 4 and 5.
- No login, no persistence; refreshing clears the conversation.

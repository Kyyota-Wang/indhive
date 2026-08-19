# INDHIVE

A demonstration of automated FDA IND **Module 1** preparation.

Synthetic sponsor, product, protocol and plan records go in. A deterministic pipeline
normalises them into one canonical record and maps that into Module 1 artifacts. Every
value keeps the source record it came from. Where two records disagree, the value is left
empty and flagged — the system does not choose.

**Nothing here is submittable to FDA.** All ten cases are fictional, and this is a proof of
concept, not regulatory software.

---

## Two halves

```
Data/POC data/          the pipeline — the only implementation of the logic
        │
        │  python run_poc.py --all        generate artifacts for all 10 cases
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

Ten cases: six clean, two with missing data (IND002, IND008), two with conflicting sources
(IND003, IND009), one with unusual formatting (IND010). Section 1.20 is supplied for four
cases only, so the gap analysis differs case to case.

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
cd "Data/POC data" && python run_poc.py --all
cd ../../V1 && python build/bundle_cases.py
```

> On Windows, `Ctrl+C` does not always stop `workerd`. If a change appears not to take
> effect, kill the strays before restarting:
> ```powershell
> Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'workerd.exe' -or ($_.Name -in @('node.exe','cmd.exe') -and $_.CommandLine -match 'wrangler') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
> ```

## Deploy

```bash
cd V1
npx wrangler secret put ANTHROPIC_API_KEY
npm run deploy
```

Then attach the domain — either add a `routes` entry to `V1/wrangler.jsonc` or set the
custom domain in the Cloudflare dashboard.

**Before sharing the link widely**, add a Cloudflare rate-limiting rule on `/api/chat`. The
in-Worker limiter is a speed bump only: Worker isolates are ephemeral, so its counter resets.
The endpoint is unauthenticated by design.

## Not built

- **Extraction from real documents.** Source records arrive already structured. Reading them
  out of PDF, DOCX or spreadsheets is the largest missing piece.
- Form FDA 1572, Form FDA 3674, investigational drug labeling — no generators.
- eCTD packaging, Part 11 signatures, audit trail.
- Modules 2, 3, 4 and 5.
- No login, no persistence; refreshing clears the conversation.

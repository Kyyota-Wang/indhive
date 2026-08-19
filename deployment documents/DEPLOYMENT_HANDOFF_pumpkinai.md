# Pumpkin AI V4 Project, Git, and Cloudflare Handoff Guide

Last updated: 2026-08-19

Audience: another AI coding agent or developer taking over local development, GitHub synchronization, and Cloudflare deployment.

This document is intentionally stored inside the V4 Git repository so it can travel with the source code. It contains resource names and setup steps, but no real Gemini key, Cloudflare API token, Turnstile secret, or Formspree endpoint value.

## 1. Read This First

Pumpkin AI is a simple, private, conversation-first business intake website. A visitor describes a problem, the Gemini receptionist provides a useful first response and clarifies the request, and the visitor may submit a structured project summary plus the complete visible transcript to Pumpkin AI's private inbox.

The current production version is V4.

```text
Local repository root:
C:\Users\kangc\OneDrive\Documents\pumpkinsolve\V4

GitHub repository:
https://github.com/Kyyota-Wang/pumpkinai_01

Git remote:
https://github.com/Kyyota-Wang/pumpkinai_01.git

Production branch:
v4-cloudflare-worker

Cloudflare Worker:
pumpkin-ai-v4

Production domain:
https://www.pumpkinsolve.com

China test domain:
https://cn-test.pumpkinsolve.com

Workers.dev address:
https://pumpkin-ai-v4.pumpkin-ai-v2.workers.dev
```

The outer `pumpkinsolve` folder is a project workspace, but `V4` is the actual Git repository root. Run Git and deployment commands from `V4`, not from V2, V3, or the outer folder.

## 2. Stable Baselines and Change Boundaries

- V3 is the frozen, stable rollback copy. Do not edit, delete, or overwrite V3.
- V4 began as an exact copy of the accepted V3 product behavior. Cloudflare hosting, Turnstile, IP rate limiting, and anonymous analytics were added afterward.
- The user has accepted the current UI and chatbot behavior. Deployment work must not casually redesign the page, rewrite marketing text, or retune the System Prompt.
- Do not create a database of customers or transcripts. Chat history stays in the current browser session until the visitor explicitly submits it.
- D1 stores only anonymous event types and timestamps for aggregate reporting. It must not store IP addresses, chat text, names, or email addresses.
- Do not modify V3 merely to make a V4 deployment easier.

Known Git baseline when this document was written:

```text
9e19918 Email daily anonymous activity reports
b2ed543 Protect public APIs from automated abuse
b270112 Route www domain to V4 Worker
fccc46e Deploy V4 directly to Cloudflare Workers
77fd094 Make Turnstile site key reliable in production
828814c Ensure production logo loads directly
```

Known production Worker deployment ID after analytics was added:

```text
d5833a19-1ae7-4971-824c-19a25e5c95cd
```

Known pre-analytics security deployment ID:

```text
16e6ba6d-3e7c-434b-834d-df21cdc473fc
```

These IDs are historical references. Always list current Cloudflare deployments before performing a rollback.

## 3. Current Architecture

### 3.1 Technology

- React 19 and Next.js-style application code
- `vinext` for building the application into a Cloudflare-compatible Worker bundle
- Cloudflare Workers for pages, assets, and `/api/*`
- Gemini API for conversation and structured project summaries
- Conditional Google Search grounding for current-information or source-dependent questions
- Formspree for private request delivery and daily activity emails
- Cloudflare Turnstile for bot protection
- Cloudflare rate-limit bindings for per-IP chat and submission limits
- Cloudflare D1 for anonymous aggregate event counts
- Cloudflare Cron Triggers for the daily 24-hour activity report

### 3.2 Important Files

```text
V4/
|-- app/
|   |-- page.tsx                    Main one-page website
|   |-- globals.css                 Responsive layout and visual styling
|   |-- components/ChatIntake.tsx   Chat UI, Turnstile, contact and submission UI
|   |-- privacy/page.tsx
|   |-- terms/page.tsx
|   `-- disclaimer/page.tsx
|-- worker/index.ts                API routes, Gemini, Formspree, security, analytics, Cron
|-- migrations/0001_analytics.sql  D1 anonymous analytics schema
|-- tests/rendered-html.test.mjs   Build and Worker behavior tests
|-- tests/intake-evaluation.mjs    Live conversational evaluation harness
|-- public/                        Logo and social-preview assets
|-- wrangler.jsonc                 Cloudflare Worker configuration
|-- .env.example                   Local variable names only
|-- .env.local                     Local secrets; ignored by Git
|-- package.json                   Commands and fixed dependencies
`-- pnpm-lock.yaml                 Reproducible dependency lockfile
```

### 3.3 Browser and API Flow

Page request:

```text
Browser
  -> www.pumpkinsolve.com
  -> Cloudflare Worker
  -> vinext page/assets
  -> anonymous page_view event in D1
```

Chat request:

```text
Browser
  -> Turnstile one-time token
  -> POST /api/chat
  -> Cloudflare per-IP rate limit
  -> Worker verifies Turnstile token, hostname, and action
  -> Gemini, with Google Search only when routing requires it
  -> assistant response
  -> anonymous D1 metrics
  -> browser resets Turnstile for a fresh token
```

Project submission:

```text
Browser
  -> POST /api/submit with visible transcript and contact details
  -> rate limit and Turnstile verification
  -> Gemini creates the structured summary
  -> Formspree receives summary plus complete transcript
  -> UI shows success only after Formspree returns success
```

Daily analytics:

```text
Cloudflare Cron
  -> scheduled() in worker/index.ts
  -> confirm local time is 11:59 PM America/New_York
  -> count previous 24 hours in D1
  -> send report through Formspree
  -> record the report window to prevent duplicate delivery
```

## 4. What the Email Workflows Send

### 4.1 Customer Project Submission

The project email contains:

- Customer name and email
- Reply-To based on the customer's email
- Service area
- Customer type
- Problem
- Desired outcome
- What has been tried
- Timeline
- One-time, recurring, or software/Agent need type
- Budget, when provided
- Contact details
- Complete visible transcript labeled `Visitor` and `Pumpkin AI assistant`

The message must never contain Gemini credentials, Turnstile secrets, Cloudflare credentials, hidden conversation state, or another visitor's data.

### 4.2 Daily Anonymous Activity Report

The daily report contains counts for the previous 24 hours:

- Homepage views
- Conversations started
- Assistant replies delivered
- Customer requests submitted
- Requests blocked by Turnstile
- Requests blocked by IP rate limits
- Assistant errors

It does not contain IP addresses, names, emails, chat text, or customer project details.

## 5. Local Setup on This Computer

Open PowerShell and enter the actual repository root:

```powershell
Set-Location "C:\Users\kangc\OneDrive\Documents\pumpkinsolve\V4"
```

Confirm runtime versions:

```powershell
node --version
pnpm --version
git --version
```

The project declares Node `>=22.13.0`. Use the committed lockfile:

```powershell
pnpm install --frozen-lockfile
```

Create `.env.local` from `.env.example` only when it does not already exist. Never overwrite an existing `.env.local`, because it may already contain working local credentials.

Required variable names are:

```dotenv
NEXT_PUBLIC_TURNSTILE_SITE_KEY=
TURNSTILE_SECRET=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
FORMSPREE_ENDPOINT=
```

Rules:

- `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is intentionally visible in browser code.
- `TURNSTILE_SECRET`, `GEMINI_API_KEY`, and `FORMSPREE_ENDPOINT` are server-only values.
- `.env.local` is ignored by Git and must remain ignored.
- Do not reuse a `.env` file from another unrelated project.
- Do not paste real values into this guide, issues, commits, terminal screenshots, or AI chat.

Start the local app:

```powershell
pnpm run dev -- --port 3003
```

Open:

```text
http://localhost:3003
```

The port number is not a version number. Port 3003 has commonly been used for V3/V4 testing, but the code directory determines which version is running.

If a long-running dev command appears stuck, it may simply be keeping the server alive. Leave it running in its own terminal and use another terminal for tests and Git commands.

## 6. Local Verification Before Any Commit or Deployment

Run one command at a time from V4:

```powershell
pnpm run build
pnpm test
pnpm run lint
node node_modules/typescript/bin/tsc --noEmit
```

`pnpm test` already runs a build before the rendered HTML and Worker tests. The separate build command is still useful when diagnosing build failures.

For live Gemini conversation evaluation, a valid local Gemini key is required:

```powershell
pnpm run test:intake:once
```

The full repeated intake evaluation is more expensive and slower:

```powershell
pnpm run test:intake
```

Do not run multiple builds, intake suites, or dev servers against the same output directory in parallel. `vinext` may contend over generated files and make a healthy project look broken.

Manual browser checks:

1. `/` opens at the Hero rather than jumping to chat.
2. `/#chat` opens the chat section.
3. English and Chinese messages receive appropriate replies.
4. Turnstile completes and refreshes between API calls.
5. A multi-turn conversation remembers prior details.
6. `Create Summary & Send` sends the summary and complete transcript.
7. The mobile layout works at approximately `390 x 844`.
8. The desktop layout works at approximately `1440 x 900`.
9. The page has no horizontal overflow or overlapping controls.

## 7. Clone the Repository on Another Computer

Use the real GitHub URL:

```powershell
git clone https://github.com/Kyyota-Wang/pumpkinai_01.git
Set-Location pumpkinai_01
git switch v4-cloudflare-worker
git pull --ff-only origin v4-cloudflare-worker
pnpm install --frozen-lockfile
```

The repository's default branch may not be the production V4 branch. Always confirm the active branch before editing or deploying:

```powershell
git status --short --branch
git branch -vv
git remote -v
```

Expected remote:

```text
origin  https://github.com/Kyyota-Wang/pumpkinai_01.git
```

If Git reports `detected dubious ownership` on this OneDrive folder, review the path and then mark only this repository as safe:

```powershell
git config --global --add safe.directory "C:/Users/kangc/OneDrive/Documents/pumpkinsolve/V4"
```

Do not mark all directories safe.

## 8. Git Workflow Used for This Project

### 8.1 Inspect Before Editing

```powershell
git status --short --branch
git remote -v
git fetch origin
git log --oneline --decorate -10
git log --oneline --left-right HEAD...origin/v4-cloudflare-worker
```

If the working tree is clean and the remote branch is ahead, update without creating a merge commit:

```powershell
git pull --ff-only origin v4-cloudflare-worker
```

If the working tree contains changes, inspect and preserve them. Do not use `git reset --hard`, `git clean -fd`, or `git checkout -- .` to make the warning disappear.

### 8.2 Review Changes

```powershell
git status --short
git diff --stat
git diff
```

Confirm that none of these are staged:

- `.env.local`
- `.wrangler/`
- `node_modules/`
- `dist/`
- `.vinext/`
- `outputs/`
- logs, screenshots, temporary files, or real credentials

### 8.3 Stage Intentionally

Prefer explicit paths instead of blindly staging everything:

```powershell
git add worker/index.ts wrangler.jsonc tests/rendered-html.test.mjs
```

For this document alone:

```powershell
git add DEPLOYMENT_HANDOFF_pumpkinai.md
```

Then inspect the exact staged patch:

```powershell
git diff --cached --check
git diff --cached --stat
git diff --cached
```

### 8.4 Commit

Use a short imperative message that describes the actual change:

```powershell
git commit -m "Document Git and Cloudflare handoff"
```

Confirm the commit:

```powershell
git log --oneline -3
git status --short --branch
```

### 8.5 Push to GitHub

Push the V4 branch explicitly:

```powershell
git push origin v4-cloudflare-worker
```

For a freshly created local branch, set upstream once:

```powershell
git push -u origin v4-cloudflare-worker
```

GitHub authentication on Windows normally uses Git Credential Manager and opens a browser login. A GitHub personal access token may be used when required, but it must be entered through the credential prompt and never embedded in the remote URL or committed to a file.

After pushing:

```powershell
git status --short --branch
git log --oneline origin/v4-cloudflare-worker -3
```

Expected status is clean and aligned with `origin/v4-cloudflare-worker`.

### 8.6 Important: Git Push Is Not Deployment

This project currently uses manual Wrangler deployment. Pushing to GitHub does not automatically update Cloudflare.

There is no approved GitHub Actions or Cloudflare Git integration pipeline in this repository. Another AI must not assume that a successful `git push` changed `www.pumpkinsolve.com`.

The safe release sequence is:

1. Pull the current production branch with `--ff-only`.
2. Make focused changes.
3. Run build, tests, lint, TypeScript, and browser checks.
4. Review and commit locally.
5. Deploy that exact committed tree to Cloudflare.
6. Run production smoke tests.
7. Push the verified commit to GitHub.
8. Record the commit and Cloudflare deployment/version ID.

If organizational policy requires pushing before deployment, that is acceptable, but still deploy the exact tested commit and record both identifiers.

Never force-push the production branch.

## 9. Cloudflare Authentication Options

There are two supported approaches. Use one, not both at the same time unless troubleshooting.

### 9.1 Interactive Wrangler OAuth

From V4:

```powershell
pnpm exec wrangler login
```

Wrangler opens a browser. Sign in to the Cloudflare account that owns `pumpkinsolve.com`, approve Wrangler, and wait for the terminal to say `Successfully logged in`.

If Wrangler then asks whether to install optional Cloudflare skills for AI coding agents, that is unrelated to account authorization. Answering `n` does not undo the successful login.

Verify the session:

```powershell
pnpm exec wrangler whoami
```

The expected account ID is already declared in `wrangler.jsonc`:

```text
bd61a7a5c0e63e9a5c05f70fb97a9b97
```

### 9.2 Scoped Cloudflare API Token

Use a scoped token for a non-interactive AI or CI-like handoff. Do not give another AI the Global API Key.

Cloudflare dashboard path:

1. Sign in to Cloudflare.
2. Open the profile menu.
3. Open `My Profile`.
4. Open `API Tokens`.
5. Select `Create Token`.

Direct page:

```text
https://dash.cloudflare.com/profile/api-tokens
```

Use a custom token restricted to the one Cloudflare account and the `pumpkinsolve.com` zone. Grant only the capabilities needed for the planned work. Typical deployment permissions are:

- Account / Workers Scripts / Edit
- Zone / Workers Routes / Edit for `pumpkinsolve.com`
- Account / Account Settings / Read
- Account / D1 / Edit only when creating, migrating, or querying D1
- Account / Turnstile / Edit only when changing the Turnstile widget

Cloudflare permission labels can evolve. Select the narrow equivalent permissions shown in the current dashboard and avoid unrelated account-wide write access.

Copy the token once and store it in a password manager. Do not place it in `.env.local`; `.env.local` contains application runtime values and is not the correct home for a Cloudflare deployment credential.

For one PowerShell session:

```powershell
$env:CLOUDFLARE_API_TOKEN = "PASTE_SCOPED_TOKEN_HERE"
$env:CLOUDFLARE_ACCOUNT_ID = "bd61a7a5c0e63e9a5c05f70fb97a9b97"
pnpm exec wrangler whoami
```

Clear the session value when finished:

```powershell
Remove-Item Env:CLOUDFLARE_API_TOKEN
```

Do not print the token with `Get-ChildItem Env:` or include it in command logs sent to another AI.

## 10. Credential Boundaries

These values have different jobs:

| Value | Purpose | Public? | Storage |
|---|---|---:|---|
| `CLOUDFLARE_API_TOKEN` | Authorizes Wrangler to manage Cloudflare | No | Temporary shell or secure CI secret |
| `GEMINI_API_KEY` | Worker calls Gemini | No | Cloudflare Worker secret and local `.env.local` |
| `FORMSPREE_ENDPOINT` | Worker sends project and analytics email | No | Cloudflare Worker secret and local `.env.local` |
| `TURNSTILE_SECRET` | Worker verifies Turnstile responses | No | Cloudflare Worker secret and local `.env.local` |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Browser renders Turnstile | Yes | Public build configuration/fallback |
| `TURNSTILE_HOSTNAMES` | Allowed production hosts | Yes | `wrangler.jsonc` variable |

Do not confuse the Cloudflare API token with the Turnstile secret. Do not use the Gemini key as a client-side environment variable.

## 11. Configure Worker Secrets

The Worker already exists. Secrets are entered interactively and are not written to Git:

```powershell
pnpm exec wrangler secret put GEMINI_API_KEY
pnpm exec wrangler secret put FORMSPREE_ENDPOINT
pnpm exec wrangler secret put TURNSTILE_SECRET
```

Paste each value only when Wrangler prompts for it.

List secret names without revealing values:

```powershell
pnpm exec wrangler secret list
```

Expected server-side secret names:

```text
GEMINI_API_KEY
FORMSPREE_ENDPOINT
TURNSTILE_SECRET
```

The Gemini model is a non-secret Worker variable in `wrangler.jsonc`:

```text
gemini-3.5-flash-lite
```

## 12. Turnstile Configuration

The public site key and private secret must belong to the same Turnstile widget.

In the Cloudflare dashboard:

1. Open `Turnstile` under Application Security.
2. Open the Pumpkin AI widget.
3. Confirm allowed hostnames include:
   - `www.pumpkinsolve.com`
   - `cn-test.pumpkinsolve.com`
4. Copy the site key for the browser configuration.
5. Store the secret with `wrangler secret put TURNSTILE_SECRET`.

The Worker also checks the hostname against:

```text
TURNSTILE_HOSTNAMES=www.pumpkinsolve.com,cn-test.pumpkinsolve.com
```

Turnstile tokens are one-time and short-lived. The browser must reset the widget after an API call. Reusing a token can make the second chat message fail even when the first succeeds.

Production should fail closed: missing or invalid Turnstile validation must not silently grant Gemini access.

## 13. IP Rate Limits

The current `wrangler.jsonc` bindings are:

```text
CHAT_RATE_LIMITER:   8 requests per 60 seconds per IP
SUBMIT_RATE_LIMITER: 2 requests per 60 seconds per IP
```

These limits protect Gemini and Formspree from automated abuse. The Gemini provider spend cap remains the last financial safeguard, not the first defense.

If limits are changed, update tests and verify both a normal multi-turn conversation and a deliberate rate-limit case. Do not remove rate limiting to solve a transient test problem.

## 14. D1 Anonymous Analytics

Current database:

```text
Database name: pumpkin-ai-analytics
Binding: ANALYTICS_DB
Database ID: d71657d8-2e93-4008-94fe-2023cd6526af
Migration: migrations/0001_analytics.sql
```

For a fresh Cloudflare account only, create the database:

```powershell
pnpm exec wrangler d1 create pumpkin-ai-analytics
```

Then place the returned database ID in `wrangler.jsonc`. Do not replace the existing production ID when deploying to the established account.

Apply the committed migration to the remote database:

```powershell
pnpm exec wrangler d1 migrations apply pumpkin-ai-analytics --remote
```

Inspect migration state:

```powershell
pnpm exec wrangler d1 migrations list pumpkin-ai-analytics --remote
```

Example privacy check:

```powershell
pnpm exec wrangler d1 execute pumpkin-ai-analytics --remote --command "SELECT metric, COUNT(*) AS total FROM analytics_events GROUP BY metric ORDER BY metric"
```

The schema may contain metric, timestamp, and report-window bookkeeping. It must not be extended to store visitor identity or conversation contents without a separately approved privacy redesign.

## 15. Daily Report Schedule

The business requirement is one report at 11:59 PM in `America/New_York`, including the previous 24 hours.

Cloudflare Cron uses UTC and does not automatically follow daylight saving time. `wrangler.jsonc` therefore registers both candidate UTC schedules:

```text
59 3 * * *
59 4 * * *
```

The Worker checks the configured `REPORT_TIME_ZONE` and sends only when local New York time is 11:59 PM. D1 report-window bookkeeping prevents duplicate delivery.

Do not simplify the two Cron entries to one fixed UTC time unless the business explicitly accepts daylight-saving drift.

The report uses the same server-side Formspree endpoint as customer submissions. Formspree must remain configured for both features.

## 16. Cloudflare Domains and the China-Access Lesson

V4 is deployed directly from the owner's Cloudflare account. Current custom domains are declared in `wrangler.jsonc`:

```text
www.pumpkinsolve.com
cn-test.pumpkinsolve.com
```

Earlier, the custom domain ultimately pointed to a `chatgpt.site` origin. A user in mainland China reached a Cloudflare block page stating that access to `chatgpt.site` was blocked. The problem was not the Pumpkin AI page code or a CSS performance warning; it was the upstream hosting path.

The fix was to make the V4 Cloudflare Worker the direct origin for `www.pumpkinsolve.com`. Do not restore a CNAME or routing dependency to `chatgpt.site`.

Domestic verification must test the entire workflow, not only the HTML:

1. Homepage opens without the old block page.
2. Logo and CSS load.
3. Turnstile loads and completes.
4. First chat message succeeds.
5. Second chat message succeeds with a fresh token.
6. Summary submission succeeds.

Passing a US browser check does not prove mainland-China usability. Keep `cn-test.pumpkinsolve.com` available for isolated diagnostics unless the owner explicitly removes it.

## 17. Deploy to Cloudflare

First confirm that the correct committed code is checked out:

```powershell
git status --short --branch
git log --oneline -1
pnpm exec wrangler whoami
```

Then deploy using the repository script:

```powershell
pnpm run deploy:cloudflare
```

Use this script instead of calling raw `wrangler deploy` directly. `vinext deploy` performs the framework build and packages the correct Worker and static assets.

The expected deployment name is:

```text
pumpkin-ai-v4
```

Record from the command output:

- Git commit hash
- Cloudflare version or deployment ID
- Deployment time
- Domains included
- Whether D1 migrations were applied

Do not change DNS records simply because deployment output is unfamiliar. Inspect the current Worker custom-domain state first.

## 18. Production Smoke Tests

After deployment, check all three addresses:

```text
https://www.pumpkinsolve.com
https://cn-test.pumpkinsolve.com
https://pumpkin-ai-v4.pumpkin-ai-v2.workers.dev
```

Required checks:

1. Homepage returns successfully and shows the accepted V4 UI.
2. Logo is sharp and loads from the Worker assets.
3. Privacy, Terms, and Disclaimer pages open.
4. A Turnstile-protected English chat succeeds.
5. A second turn succeeds and remembers the first.
6. A Chinese chat succeeds.
7. An API request without a valid Turnstile token is rejected.
8. Repeated requests eventually trigger the configured IP limit.
9. A clearly labeled test project submission reaches the Formspree inbox with summary and complete transcript.
10. D1 receives anonymous metrics only.
11. The scheduled report can be tested without exposing customer data.
12. A mainland-China user verifies the full two-turn chat and submission path.

Do not declare production complete solely because the homepage returned HTTP 200.

## 19. Inspect Cloudflare Logs and State

Tail live Worker logs during a controlled test:

```powershell
pnpm exec wrangler tail pumpkin-ai-v4
```

List deployments or versions using the current Wrangler commands:

```powershell
pnpm exec wrangler deployments list
pnpm exec wrangler versions list
```

Wrangler command names can change between versions. This repository pins Wrangler through `pnpm-lock.yaml`; use the local `pnpm exec wrangler`, not an unrelated global installation.

When logging, never print request bodies, secrets, customer contact data, or full transcripts.

## 20. Rollback

There are two rollback layers.

### 20.1 Worker Version Rollback

List current versions first:

```powershell
pnpm exec wrangler versions list
pnpm exec wrangler deployments list
```

Use the rollback command supported by the pinned Wrangler version and select the last known good Worker version. Verify the target ID before confirming.

After rollback, rerun production smoke tests. A Worker rollback does not automatically reverse D1 schema changes.

### 20.2 V3 Product Fallback

V3 is the frozen pre-V4 product snapshot. If V4 cannot be stabilized quickly, V3 remains the source-level fallback. Switching production back to V3 is a deliberate deployment and routing action; never overwrite V3 with V4 files.

Before any risky V4 release, keep these facts recorded:

- Last known good V4 Git commit
- Last known good Worker version/deployment ID
- Current D1 migration state
- Current custom-domain routes
- Current Turnstile hostnames
- V3 location and hosting status

## 21. Common Failure Modes

### `The assistant is temporarily unavailable`

Likely causes:

- Local dev server started from the wrong folder
- Missing local `GEMINI_API_KEY`
- Old process still owns the port
- Frontend and Worker are not being served by the same local process
- Production Worker secret missing

Check the terminal output and Worker logs. Do not hide the error by claiming submission succeeded.

### First chat message works, second fails

Likely cause: Turnstile token reuse. Confirm that the widget resets and produces a fresh token after every API request.

### Page works but no email arrives

Check:

- Browser showed delivered only after `/api/submit` succeeded
- `FORMSPREE_ENDPOINT` exists as a Worker secret
- Formspree submission log contains the request
- Destination email and spam folder
- Formspree account or form limits
- Worker logs for a non-2xx Formspree response

### Git push succeeds but website is unchanged

Expected with the current setup. GitHub push and Cloudflare deployment are separate. Run the tested `pnpm run deploy:cloudflare` process.

### Cloudflare login browser says authorization granted but terminal waits

Return to the terminal. It may already say `Successfully logged in` and be waiting on an optional Wrangler question. Answer that question, then run `pnpm exec wrangler whoami`.

### Mainland user sees `unable to access chatgpt.site`

The domain is still routed through the old upstream. Confirm `www.pumpkinsolve.com` is attached directly to `pumpkin-ai-v4` and remove any obsolete CNAME/deployment dependency only after inspecting current DNS and Worker routes.

### Lighthouse reports hundreds of KiB of unused JavaScript from `chrome-extension://`

That code belongs to browser extensions, not Pumpkin AI. Retest in Incognito with extensions disabled before changing the app.

### Lighthouse reports a 512x512 logo transferred for a 34x34 display

Use an appropriately sized modern image variant or responsive source. Treat it as a performance improvement, not the cause of the China block page.

## 22. Release Checklist

Before deployment:

- [ ] Running commands from the V4 repository root
- [ ] Active branch is `v4-cloudflare-worker`
- [ ] Local branch is synchronized with `origin/v4-cloudflare-worker`
- [ ] V3 remains untouched
- [ ] Working tree changes are understood
- [ ] No secrets or `.env.local` are staged
- [ ] Build passes
- [ ] Tests pass
- [ ] ESLint passes
- [ ] TypeScript passes
- [ ] Desktop and mobile checks pass
- [ ] Multi-turn English and Chinese chat checks pass
- [ ] Commit hash recorded
- [ ] Correct Cloudflare account confirmed with `wrangler whoami`
- [ ] Worker secret names are present
- [ ] D1 migrations are current
- [ ] Turnstile hostnames are correct

After deployment:

- [ ] Worker deployment/version ID recorded
- [ ] `www.pumpkinsolve.com` opens
- [ ] `cn-test.pumpkinsolve.com` opens
- [ ] Workers.dev address opens
- [ ] Turnstile rejects missing/invalid tokens
- [ ] Two-turn chat succeeds
- [ ] Chinese chat succeeds
- [ ] Rate limiting works
- [ ] Test submission reaches the inbox with transcript
- [ ] D1 stores only anonymous event data
- [ ] Daily report behavior is verified
- [ ] Mainland-China full workflow is verified
- [ ] Verified commit is pushed to GitHub
- [ ] Git working tree is clean

## 23. Instructions for the Next AI

1. Read this document and `README.md` before touching code.
2. Treat `V4` as the Git and deployment root.
3. Inspect Git status before editing; preserve unknown user changes.
4. Never reveal or commit credentials.
5. Keep V3 frozen.
6. Keep the accepted UI and conversation behavior unless the user explicitly requests a product change.
7. Make the smallest change needed for the stated task.
8. Run verification before deployment.
9. Remember that Git push does not deploy this project.
10. Deploy the exact tested commit with `pnpm run deploy:cloudflare`.
11. Verify the complete protected chat and email path, not just page availability.
12. Record the Git commit and Worker deployment ID so rollback remains possible.

## 24. Fast Command Reference

```powershell
# Enter the repo
Set-Location "C:\Users\kangc\OneDrive\Documents\pumpkinsolve\V4"

# Inspect Git
git status --short --branch
git remote -v
git fetch origin
git pull --ff-only origin v4-cloudflare-worker

# Install and verify
pnpm install --frozen-lockfile
pnpm run build
pnpm test
pnpm run lint
node node_modules/typescript/bin/tsc --noEmit

# Local app
pnpm run dev -- --port 3003

# Cloudflare auth
pnpm exec wrangler login
pnpm exec wrangler whoami

# Secret names
pnpm exec wrangler secret list

# D1
pnpm exec wrangler d1 migrations list pumpkin-ai-analytics --remote
pnpm exec wrangler d1 migrations apply pumpkin-ai-analytics --remote

# Deploy
pnpm run deploy:cloudflare

# Observe
pnpm exec wrangler tail pumpkin-ai-v4
pnpm exec wrangler deployments list
pnpm exec wrangler versions list

# Commit and push
git add <explicit-files>
git diff --cached --check
git diff --cached
git commit -m "Describe the focused change"
git push origin v4-cloudflare-worker
```

End of handoff guide.

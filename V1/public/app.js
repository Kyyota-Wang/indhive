const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const state = {
  cases: [],
  current: null,
  view: null,       // null = home, otherwise a module id
  letters: {},
  openField: null,
  messages: [],
  busy: false,
};

const ICON = {
  form: '<svg viewBox="0 0 20 20" width="19" height="19"><rect x="3.5" y="2.5" width="13" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.5 7h7M6.5 10h7M6.5 13h4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
  letter: '<svg viewBox="0 0 20 20" width="19" height="19"><rect x="2.5" y="4.5" width="15" height="11" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M3 6l7 5 7-5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  plan: '<svg viewBox="0 0 20 20" width="19" height="19"><path d="M3 16V8M7.7 16V4M12.3 16v-6M17 16v-9" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>',
  toc: '<svg viewBox="0 0 20 20" width="19" height="19"><path d="M3.5 5h2M3.5 10h2M3.5 15h2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><path d="M8.5 5h8M8.5 10h8M8.5 15h5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
  inbox: '<svg viewBox="0 0 20 20" width="19" height="19"><path d="M2.5 12h4l1 2h5l1-2h4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4.2 3.5h11.6l1.7 8.5v4a1 1 0 0 1-1 1H3.5a1 1 0 0 1-1-1v-4z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>',
  check: '<svg viewBox="0 0 20 20" width="19" height="19"><path d="M10 2.5l6 2.5v5c0 3.4-2.4 6.4-6 7.5-3.6-1.1-6-4.1-6-7.5V5z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M7.3 10l1.9 2 3.5-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
};

const fieldCount = (c) => c.source_records.reduce((n, r) => n + Object.keys(r.fields).length, 0);
const contestedPaths = (c) => new Set(c.conflicts.map((x) => x.field));

const MODULES = [
  {
    id: "input", kind: "input", title: "Source input", icon: ICON.inbox,
    desc: "The records supplied for this case, and where each field ended up.",
    read: (c) => {
      const contested = c.source_records.reduce(
        (n, r) => n + Object.keys(r.fields).filter((p) => contestedPaths(c).has(p)).length,
        0,
      );
      return {
        stat: `${c.source_records.length} records · ${fieldCount(c)} fields`,
        state: contested ? [`${contested} contested`, "warn"] : ["no disagreement", "ok"],
      };
    },
  },
  {
    id: "form_1571", kind: "output", title: "Form FDA 1571", icon: ICON.form,
    desc: "Sponsor, product, protocol and submission fields mapped to their real box numbers.",
    read: (c) => {
      const total = c.form_1571.length;
      const bad = c.form_1571.filter((f) => f.status === "CONFLICT" || f.status === "MISSING").length;
      return {
        stat: `${total} fields mapped`,
        state: bad ? [`${bad} unresolved`, "bad"] : ["all mapped", "ok"],
      };
    },
  },
  {
    id: "cover_letter", kind: "output", title: "Cover letter", icon: ICON.letter,
    desc: "Drafted from an approved fact list, then checked for anything the sources do not support.",
    read: (c) => {
      const held = state.letters[c.case_id];
      if (!held) return { stat: "Not drafted yet", state: ["draft on open", "idle"] };
      const g = held.grounding;
      return {
        stat: `${g.facts_present} of ${g.facts_total} facts used`,
        state: g.status === "clean" ? ["grounded", "ok"] : [`${g.unsupported.length} unverified`, "warn"],
      };
    },
  },
  {
    id: "plan", kind: "output", title: "1.20 Investigational plan", icon: ICON.plan,
    desc: "The six elements required by 21 CFR 312.23(a)(3)(iv), plus the studies planned for year one.",
    read: (c) => {
      const s = c.investigational_plan.summary;
      return {
        stat: `${s.elements_present} of ${s.elements_total} elements`,
        state: s.elements_missing ? [`${s.elements_missing} missing`, "warn"] : ["complete", "ok"],
      };
    },
  },
  {
    id: "toc", kind: "output", title: "Module 1 gap analysis", icon: ICON.toc,
    desc: "The US regional Module 1 skeleton, with every section resolved against this case.",
    read: (c) => {
      const s = c.toc.summary;
      return {
        stat: `${s.required_present} of ${s.required_total} required present`,
        state: s.required_absent ? [`${s.required_absent} outstanding`, "warn"] : ["complete", "ok"],
      };
    },
  },
  {
    id: "validation", kind: "output", title: "Validation", icon: ICON.check,
    desc: "Field presence, source conflicts and cross-document consistency, deduplicated.",
    read: (c) => {
      const blocking = c.validation.issues.filter((i) => i.status === "MISSING" || i.status === "CONFLICT").length;
      const passed = c.validation.issues.filter((i) => i.status === "PASS").length;
      return {
        stat: `${passed} checks passed`,
        state: blocking ? [`${blocking} blocking`, "bad"] : ["no blockers", "ok"],
      };
    },
  },
];

const moduleById = (id) => MODULES.find((m) => m.id === id);

/* ---------------- data ---------------- */

async function loadCases() {
  const data = await (await fetch("/api/cases")).json();
  state.cases = data.cases || [];
  $("cases").innerHTML = state.cases
    .map((c) => {
      const product = (c.label.split(" - ")[1] || "").split(" ")[0];
      const kind = c.scenario_type;
      const tag =
        kind === "clean"
          ? ""
          : `<span class="tag ${kind === "unusual_formatting" ? "unusual" : kind}">${esc(
              kind === "unusual_formatting" ? "formatting" : kind,
            )}</span>`;
      return `<button class="casebtn" data-id="${c.case_id}">
          <span class="cid">${c.case_id}</span><span class="prod">${esc(product)}</span>${tag}
        </button>`;
    })
    .join("");
  $("cases").querySelectorAll(".casebtn").forEach((b) => (b.onclick = () => selectCase(b.dataset.id)));
  if (state.cases.length) await selectCase(state.cases[0].case_id);
}

async function selectCase(id) {
  const res = await fetch(`/api/case/${id}`);
  if (!res.ok) return;
  state.current = await res.json();
  state.openField = null;
  $("cases").querySelectorAll(".casebtn").forEach((b) => b.classList.toggle("active", b.dataset.id === id));
  render();
}

/* ---------------- starter questions ---------------- */

// Three, and every one of them names the case currently on screen. A chip that
// says "which value is correct?" without saying which value leaves the assistant
// guessing at the referent and the reader guessing at what the click will do.
function starterQuestions(c) {
  const chips = [
    { label: "How do I use this?", ask: "What can this platform do, and how do I use this page?" },
    {
      label: `How was ${c.case_id} built?`,
      ask: `Show me how ${c.case_id} was built, from its source records through to the artifacts.`,
    },
  ];

  // The refusal only lands on a case that actually has competing values; a clean
  // case gets a question with a real answer instead.
  chips.push(
    c.conflicts.length
      ? {
          label: "Which sponsor name is right?",
          ask: `Which sponsor name is the correct one for ${c.case_id}?`,
        }
      : {
          label: `What would ${c.case_id} still need?`,
          ask: `What would ${c.case_id} still need before it could be filed?`,
        },
  );
  return chips;
}

function renderStarters(c) {
  const el = $("starters");
  if (state.messages.length) return; // gone for the session once a conversation starts
  el.innerHTML = starterQuestions(c)
    .map((q) => `<button class="chip" data-ask="${esc(q.ask)}">${esc(q.label)}</button>`)
    .join("");
}

/* ---------------- navigation ---------------- */

function showHome() {
  state.view = null;
  render();
}

function showDetail(id) {
  state.view = id;
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function render() {
  const c = state.current;
  if (!c) return;

  renderStarters(c);

  const home = state.view === null;
  $("view-home").hidden = !home;
  $("view-detail").hidden = home;
  $("crumbs").hidden = home;

  if (home) {
    $("case-caption").textContent = `Generated from the ${c.source_records.length} source records supplied for ${c.case_id}.`;
    $("hero-cta").textContent = `See what it generated for ${c.case_id}`;
    const card = (m) => {
      const { stat, state: st } = m.read(c);
      return `<button class="modcard ${m.kind}" data-mod="${m.id}">
          <span class="ic">${m.icon}</span>
          <h3>${esc(m.title)}</h3>
          <span class="desc">${esc(m.desc)}</span>
          <span class="foot"><span class="stat">${esc(stat)}</span><span class="state ${st[1]}">${esc(st[0])}</span></span>
        </button>`;
    };
    $("input-grid").innerHTML = MODULES.filter((m) => m.kind === "input").map(card).join("");
    $("modules").innerHTML = MODULES.filter((m) => m.kind === "output").map(card).join("");
    document
      .querySelectorAll("#input-grid .modcard, #modules .modcard")
      .forEach((el) => (el.onclick = () => showDetail(el.dataset.mod)));
    return;
  }

  const mod = moduleById(state.view);
  $("crumb-now").textContent = mod.title;
  $("detail-title").textContent = mod.title;
  $("detail-sub").textContent = `${c.case_id} · ${c.label.split(" - ").slice(1).join(" - ")}`;
  $("detail-jump").innerHTML = MODULES.map(
    (m) => `<button class="jump ${m.id === state.view ? "active" : ""}" data-mod="${m.id}">${esc(m.title)}</button>`,
  ).join("");
  $("detail-jump").querySelectorAll(".jump").forEach((el) => (el.onclick = () => showDetail(el.dataset.mod)));

  if (state.view === "input") renderInput(c);
  else if (state.view === "form_1571") renderForm(c);
  else if (state.view === "cover_letter") renderLetter(c);
  else if (state.view === "plan") renderPlan(c);
  else if (state.view === "toc") renderToc(c);
  else renderValidation(c);

  const showRail = state.view === "form_1571";
  $("rail").hidden = !showRail;
  if (showRail) renderRail(c);
}

function renderRail(c) {
  const lit = new Set();
  if (state.openField) {
    const f = c.form_1571.find((x) => x.canonical_path === state.openField);
    (f?.provenance?.sources || []).forEach((s) => lit.add(s.record_id));
  }
  $("rail-items").innerHTML = c.source_records
    .map(
      (r) => `<div class="recitem ${lit.has(r.record_id) ? "lit" : ""}">
        <div class="rid">${esc(r.record_id)}</div>
        <div class="rmeta">${Object.keys(r.fields).length} fields</div></div>`,
    )
    .join("");
}

/* ---------------- input view ---------------- */

// Where a supplied field ends up. This is the whole point of the input view:
// every row states which output consumed it, or says plainly that none did.
function destinationOf(c, path) {
  const f = c.form_1571.find((x) => x.canonical_path === path);
  if (f) {
    return f.box
      ? { label: `Form 1571 · Box ${f.box}`, view: "form_1571", field: path }
      : { label: "Form 1571 · supporting data", view: "form_1571", field: path };
  }
  if (path.startsWith("plan.")) return { label: "1.20 Investigational plan", view: "plan" };
  // Investigator contact details belong on Form FDA 1572, which has no generator yet —
  // so the input carries them and nothing consumes them. Say which gap that is.
  if (path.startsWith("investigator.")) return { label: "Form 1572 — no generator", view: null };
  return { label: "not used by any current output", view: null };
}

function renderInput(c) {
  const contested = contestedPaths(c);
  const conflictByPath = Object.fromEntries(c.conflicts.map((x) => [x.field, x]));
  const contestedCount = c.source_records.reduce(
    (n, r) => n + Object.keys(r.fields).filter((p) => contested.has(p)).length,
    0,
  );

  const boundary = `<div class="boundary">
      <strong>These are already-extracted structured records.</strong>
      Reading them out of real PDF, DOCX or spreadsheet source documents is not part of this
      demonstration — that extraction layer is not built. What is shown below is the input the
      pipeline actually consumes.
    </div>`;

  const bar = `<div class="statbar">
      <div class="statbox"><b>${c.source_records.length}</b><span>source records</span></div>
      <div class="statbox"><b>${fieldCount(c)}</b><span>fields supplied</span></div>
      <div class="statbox"><b>${contestedCount}</b><span>contested by another record</span></div>
    </div>`;

  const records = c.source_records
    .map((r) => {
      const rows = Object.entries(r.fields)
        .map(([path, value]) => {
          const isConflict = contested.has(path);
          const dest = destinationOf(c, path);
          const shown = value === null || value === "" ? "—" : String(value);
          const destCell = dest.view
            ? `<button class="dest" data-view="${dest.view}" data-field="${esc(dest.field || "")}">${esc(dest.label)}</button>`
            : `<span class="dest none">${esc(dest.label)}</span>`;

          let clash = "";
          if (isConflict) {
            const others = conflictByPath[path].values.filter((v) => v.record_id !== r.record_id);
            clash = others
              .map(
                (v) => `<div class="clash">contested by <code>${esc(v.record_id)}</code>, which supplies
                  “${esc(v.value)}” — left unresolved</div>`,
              )
              .join("");
          }

          return `<div class="frow ${isConflict ? "contested" : ""}">
              <span class="fpath">${esc(path)}</span>
              <span class="fvalue">${esc(shown)}${clash}</span>
              <span class="fdest">${isConflict ? `<span class="pill CONFLICT">CONFLICT</span>` : destCell}</span>
            </div>`;
        })
        .join("");

      const studies = (r.planned_studies || []).length;
      return `<div class="recgroup">
          <div class="rechead">
            <div><h5>${esc(r.title || r.record_id)}</h5>
              <span class="recmeta"><code>${esc(r.record_id)}</code>${
                r.record_type && r.record_type !== r.record_id ? " · " + esc(r.record_type) : ""
              }</span></div>
            <span class="state idle">${Object.keys(r.fields).length} fields${
              studies ? ` · ${studies} study` : ""
            }</span>
          </div>${rows}</div>`;
    })
    .join("");

  $("pane").innerHTML = boundary + bar + records;

  $("pane").querySelectorAll(".dest").forEach((el) => {
    if (!el.dataset.view) return;
    el.onclick = () => {
      state.openField = el.dataset.field || null;
      showDetail(el.dataset.view);
    };
  });
}

/* ---------------- artifact views ---------------- */

const byBox = (a, b) => Number(a.box) - Number(b.box);

function formRow(c, f) {
  const open = state.openField === f.canonical_path;
  const conflict = c.conflicts.find((x) => x.field === f.canonical_path);
  const box = f.box ? `<span class="fbox">Box ${esc(f.box)}</span>` : "";

  if (f.kind === "checklist") {
    const items = f.items
      .map(
        (i) => `<div class="ckrow ${i.checked ? "on" : ""}">
          <span class="ckbox">${i.checked ? "✓" : ""}</span>
          <span class="cknum">${esc(i.number)}.</span>
          <span><span class="cklabel">${esc(i.label)}</span><span class="cknote">${esc(i.note)}</span></span>
        </div>`,
      )
      .join("");
    return `<div class="card">
      <div class="fhead"><span class="flabel">${box}${esc(f.label)}</span>
      <span class="pill PASS">${esc(f.value)}</span></div>
      <div class="cklist">${items}</div>
      <div class="fsrc">${esc(f.message || "")}</div></div>`;
  }

  const val =
    f.value !== null && f.value !== ""
      ? `<div class="fval">${esc(f.value)}</div>`
      : `<div class="fval none">—</div>`;

  let extra = "";
  if (open && conflict) {
    extra =
      conflict.values
        .map((v) => `<div class="alt">${esc(v.value)}<div class="from">${esc(v.record_id)}</div></div>`)
        .join("") + `<div class="refuse">Unresolved. The system does not select between conflicting sources.</div>`;
  } else if (open) {
    const srcs = (f.provenance?.sources || []).map((s) => `${s.record_id} → ${s.field}`);
    const derived = f.message && !f.provenance ? f.message : null;
    extra = `<div class="fsrc">${esc(
      derived || (srcs.length ? srcs.join("  ·  ") : "no source record supplied this field"),
    )}</div>`;
  }

  return `<div class="card field ${open ? "open" : ""}" data-path="${esc(f.canonical_path || "")}">
    <div class="fhead"><span class="flabel">${box}${esc(f.label)}</span>
    <span class="pill ${f.status}">${f.status}</span></div>${val}${extra}</div>`;
}

function renderForm(c) {
  const boxed = c.form_1571.filter((f) => f.box).sort(byBox);
  const context = c.form_1571.filter((f) => !f.box);

  $("pane").innerHTML =
    boxed.map((f) => formRow(c, f)).join("") +
    (context.length
      ? `<h4 class="phead">Supporting data — not a Form 1571 box</h4>
         <p class="subnote">Carried by the pipeline for other Module 1 documents. These values do
         not appear anywhere on Form FDA 1571.</p>` + context.map((f) => formRow(c, f)).join("")
      : "");

  $("pane").querySelectorAll(".field").forEach((el) => {
    el.onclick = () => {
      const p = el.dataset.path;
      if (!p) return;
      state.openField = state.openField === p ? null : p;
      render();
    };
  });
}

function renderLetter(c) {
  const held = state.letters[c.case_id];
  if (!held) {
    $("pane").innerHTML = `<div class="empty">No cover letter drafted yet.<br><br>
      <button class="btn primary" id="ask-letter">Draft it for ${c.case_id}</button></div>`;
    $("ask-letter").onclick = () => ask(`Draft the cover letter for ${c.case_id}.`);
    return;
  }
  const g = held.grounding;
  const flagged = g.status === "flagged";
  const body = flagged
    ? `<div><b>${g.unsupported.length} value(s) could not be verified against the source data.</b>
       <ul>${g.unsupported.map((u) => `<li>${esc(u.text)} — ${esc(u.kind)}</li>`).join("")}</ul></div>`
    : `<div><b>${g.facts_present} of ${g.facts_total} approved facts used.</b> No unverified values found.</div>`;
  $("pane").innerHTML =
    `<div class="ground ${g.status}"><span>${flagged ? "!" : "✓"}</span>${body}</div>` +
    `<div class="paper">${esc(held.letter)}</div>`;
}

function renderPlan(c) {
  const p = c.investigational_plan;
  const s = p.summary;
  const bar = `<div class="statbar">
      <div class="statbox"><b>${s.elements_present}/${s.elements_total}</b><span>required elements</span></div>
      <div class="statbox"><b>${s.elements_missing}</b><span>missing</span></div>
      <div class="statbox"><b>${s.studies}</b><span>${s.studies === 1 ? "study" : "studies"} described</span></div>
    </div>`;

  const elements = p.elements
    .map(
      (e) => `<div class="tocsec"><div class="leaf">
        <span class="pill ${e.status === "PRESENT" ? "PRESENT" : "MISSING"}">${esc(e.status)}</span>
        <div><div class="ltitle">${esc(e.heading)}</div>${
          e.value ? `<div class="pbody">${esc(e.value)}</div>` : `<div class="ldetail">Not supplied.</div>`
        }</div></div></div>`,
    )
    .join("");

  const studies = p.planned_studies.length
    ? `<h4 class="phead">Studies planned for the first year</h4>` +
      p.planned_studies
        .map((st) => {
          const rows = [
            ["Objectives", st.objectives],
            ["Study design", st.design],
            ["Planned sample size", st.sample_size],
            ["Study population", st.population],
            ["Study parameters", st.parameters],
            ["Status", st.status],
          ]
            .filter(([, v]) => v)
            .map(([k, v]) => `<div class="srow"><span class="skey">${esc(k)}</span><span>${esc(v)}</span></div>`)
            .join("");
          return `<div class="tocsec"><h5>${esc(st.title || st.study_id)}</h5>${rows}</div>`;
        })
        .join("")
    : "";

  $("pane").innerHTML = bar + elements + studies + `<p class="note">${esc(p.note)}</p>`;
}

function renderToc(c) {
  const s = c.toc.summary;
  const bar = `<div class="statbar">
      <div class="statbox"><b>${s.required_present}/${s.required_total}</b><span>required present</span></div>
      <div class="statbox"><b>${s.required_absent}</b><span>outstanding</span></div>
      <div class="statbox"><b>${s.needs_decision}</b><span>needs decision</span></div>
      <div class="statbox"><b>${s.not_applicable}</b><span>not applicable</span></div>
    </div>`;

  const body = (c.toc.sections || [])
    .map((sec) => {
      const rows = sec.children
        .map((leaf) => {
          const label =
            leaf.number === sec.number
              ? esc(leaf.title)
              : `<span class="lnum">${esc(leaf.number)}</span>${esc(leaf.title)}`;
          return `<div class="leaf"><span class="pill ${leaf.status.replace(/[^A-Z]/g, "")}">${esc(leaf.status)}</span>
            <div><div class="ltitle">${label}</div>${
              leaf.detail ? `<div class="ldetail">${esc(leaf.detail)}</div>` : ""
            }</div></div>`;
        })
        .join("");
      return `<div class="tocsec"><h5><span class="lnum">${esc(sec.number)}</span>${esc(sec.title)}</h5>${rows}</div>`;
    })
    .join("");

  $("pane").innerHTML = bar + body + `<p class="note">${esc(c.toc.note)}</p>`;
}

function renderValidation(c) {
  const issues = c.validation.issues;
  const blocking = issues.filter((i) => i.status === "MISSING" || i.status === "CONFLICT");
  const warnings = issues.filter((i) => i.status === "WARNING");
  const passes = issues.filter((i) => i.status === "PASS");
  const row = (i) =>
    `<div class="card issue"><span class="pill ${i.status}">${i.status}</span>
      <div><div class="imsg">${esc(i.message)}</div><div class="ifield">${esc(i.field || "")}</div></div></div>`;

  $("pane").innerHTML =
    (blocking.length
      ? `<div class="verdict bad">NOT READY — ${blocking.length} blocking issue${blocking.length > 1 ? "s" : ""}</div>`
      : `<div class="verdict ok">No blocking issues within the checks this demo performs</div>`) +
    blocking.map(row).join("") +
    warnings.map(row).join("") +
    (passes.length
      ? `<details class="passes"><summary>${passes.length} checks passed</summary><ul>${passes
          .map((p) => `<li>${esc(p.message)}</li>`)
          .join("")}</ul></details>`
      : "") +
    `<p class="scopenote">These checks cover field presence, source conflicts and cross-document consistency only. They are not a regulatory completeness review.</p>`;
}

/* ---------------- chat ---------------- */

function openChat() {
  $("chat").hidden = false;
  $("chat-fab").hidden = true;
  $("input").focus();
}
function closeChat() {
  $("chat").hidden = true;
  $("chat-fab").hidden = false;
}

function bubble(cls, html) {
  const el = document.createElement("div");
  el.className = cls;
  el.innerHTML = html;
  $("log").appendChild(el);
  $("log").scrollTop = $("log").scrollHeight;
  return el;
}

function md(text) {
  const lines = esc(text).split("\n");
  let html = "";
  let list = false;
  for (const line of lines) {
    const item = /^\s*[-*]\s+(.*)$/.exec(line);
    if (item) {
      if (!list) { html += "<ul>"; list = true; }
      html += `<li>${item[1]}</li>`;
      continue;
    }
    if (list) { html += "</ul>"; list = false; }
    if (/^\s*\|/.test(line)) { html += `<p>${line}</p>`; continue; }
    if (line.trim()) html += `<p>${line}</p>`;
  }
  if (list) html += "</ul>";
  return html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>");
}

async function ask(text) {
  openChat();
  if (state.busy || !text.trim()) return;
  state.busy = true;
  $("send").disabled = true;
  $("starters").hidden = true;

  bubble("msg user", esc(text));
  state.messages.push({ role: "user", content: text });

  let el = null;
  let acc = "";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ messages: state.messages }),
    });
    if (!res.ok || !res.body) {
      const err = await res.json().catch(() => ({ error: `Request failed (${res.status}).` }));
      bubble("errbox", esc(err.error || "Request failed."));
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop() || "";

      for (const part of parts) {
        const line = part.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;
        let evt;
        try { evt = JSON.parse(line.slice(6)); } catch { continue; }

        if (evt.type === "text") {
          acc += evt.text;
          if (!el) el = bubble("msg assistant", "");
          el.innerHTML = md(acc);
          $("log").scrollTop = $("log").scrollHeight;
        } else if (evt.type === "tool_start") {
          bubble("toolchip running", `<span class="dot"></span>${esc(evt.name)}`).dataset.toolid = evt.id || "";
        } else if (evt.type === "tool_done") {
          const chip =
            $("log").querySelector(`.toolchip[data-toolid="${CSS.escape(evt.id || "")}"]`) ||
            [...$("log").querySelectorAll(".toolchip.running")].pop();
          if (chip) {
            chip.classList.remove("running");
            if (evt.error) chip.classList.add("err");
            const extra = evt.input?.field_path || evt.input?.case_id || "";
            chip.innerHTML = `<span class="dot"></span>${esc(evt.name)}${extra ? " · " + esc(extra) : ""}`;
          }
          el = null;
          acc = "";
        } else if (evt.type === "canvas") {
          await applyCanvas(evt);
        } else if (evt.type === "error") {
          bubble("errbox", esc(evt.message));
        }
      }
    }
    if (acc) state.messages.push({ role: "assistant", content: acc });
  } catch (err) {
    bubble("errbox", esc(String(err)));
  } finally {
    state.busy = false;
    $("send").disabled = false;
  }
}

async function applyCanvas(evt) {
  if (evt.view === "cases") return;
  if (evt.view === "cover_letter") state.letters[evt.case_id] = { letter: evt.letter, grounding: evt.grounding };
  if (evt.case_id && state.current?.case_id !== evt.case_id) await selectCase(evt.case_id);
  if (evt.focus_field) state.openField = evt.focus_field;
  if (moduleById(evt.view)) showDetail(evt.view);
  else render();
}

/* ---------------- wiring ---------------- */

$("home-link").onclick = showHome;
$("crumb-back").onclick = showHome;
$("hero-cta").onclick = () => showDetail("form_1571");
document.getElementById("hero-input").onclick = () => showDetail("input");
$("chat-fab").onclick = openChat;
$("chat-close").onclick = closeChat;

$("composer").onsubmit = (e) => {
  e.preventDefault();
  const v = $("input").value;
  $("input").value = "";
  $("input").style.height = "auto";
  ask(v);
};
$("input").addEventListener("input", (e) => {
  e.target.style.height = "auto";
  e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
});
$("input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("composer").requestSubmit();
  }
});
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-ask]");
  if (el) ask(el.dataset.ask);
});

loadCases();

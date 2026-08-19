import bundle from "./cases.json";

type Any = Record<string, any>;
const CASES: Any = (bundle as Any).cases;
const ORDER: string[] = (bundle as Any).case_order;

const SECTIONS = ["sponsor", "product", "protocol", "submission", "investigator"] as const;

function caseOr404(caseId: string): Any {
  const c = CASES[String(caseId || "").toUpperCase().trim()];
  if (!c) throw new Error(`Unknown case "${caseId}". Available: ${ORDER.join(", ")}`);
  return c;
}

function scalars(canonical: Any): Any {
  const out: Any = {};
  for (const section of SECTIONS) {
    const values: Any = {};
    for (const [k, v] of Object.entries(canonical[section] || {})) {
      if (v !== null && v !== "") values[k] = v;
    }
    out[section] = values;
  }
  return out;
}

// Collapse the pipeline's repeated checks into one row per field+status.
function dedupeIssues(issues: Any[]): Any[] {
  const seen = new Set<string>();
  const out: Any[] = [];
  for (const issue of issues) {
    const key = `${issue.status}|${issue.field || ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(issue);
  }
  return out;
}

export const TOOLS = [
  {
    name: "list_cases",
    description:
      "List every synthetic IND case available in this demo, with its scenario type and validation tally. Call this first when the user has not named a case.",
    input_schema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "get_source_input",
    description:
      "Get the source records supplied for a case — the pipeline's input. Returns each record with the canonical paths it supplied, their values, and which of those are contested by another record. Use this whenever the user asks what went in, where a value originated, or how input relates to output. These records are already extracted; extraction from real documents is not part of this demo.",
    input_schema: {
      type: "object",
      properties: { case_id: { type: "string" } },
      required: ["case_id"],
    },
  },
  {
    name: "load_case",
    description:
      "Load one case: the canonical IND data produced by the deterministic pipeline, its conflicts, and the source records it was built from. Use this for general questions about a case.",
    input_schema: {
      type: "object",
      properties: { case_id: { type: "string", description: "e.g. IND001" } },
      required: ["case_id"],
    },
  },
  {
    name: "get_form_1571",
    description:
      "Get the populated Form FDA 1571 field view for a case, with real box numbers, per-field status (PASS/WARNING/MISSING/CONFLICT) and the source record behind each value.",
    input_schema: {
      type: "object",
      properties: { case_id: { type: "string" } },
      required: ["case_id"],
    },
  },
  {
    name: "get_provenance",
    description:
      "Trace one canonical field back to every source record that supplied a value for it. Use this whenever the user asks where a value came from, or why a field is blank or conflicted.",
    input_schema: {
      type: "object",
      properties: {
        case_id: { type: "string" },
        field_path: {
          type: "string",
          description: 'Dotted canonical path, e.g. "sponsor.legal_name" or "protocol.phase"',
        },
      },
      required: ["case_id", "field_path"],
    },
  },
  {
    name: "get_validation",
    description:
      "Get deduplicated validation results for a case: blocking issues (MISSING/CONFLICT) first, then warnings, then a count of passed checks.",
    input_schema: {
      type: "object",
      properties: { case_id: { type: "string" } },
      required: ["case_id"],
    },
  },
  {
    name: "get_module1_toc",
    description:
      "Get the Module 1 table of contents for a case, resolved against the US regional eCTD section structure. Every section carries a status: PRESENT, ABSENT (required but not supplied), NEEDS DECISION (conditional on facts the sponsor holds), or N/A. This is the gap analysis — use it for any question about Module 1 structure, completeness, what is missing, or what would be needed before filing.",
    input_schema: {
      type: "object",
      properties: { case_id: { type: "string" } },
      required: ["case_id"],
    },
  },
  {
    name: "get_investigational_plan",
    description:
      "Get Module 1.20, the General Investigational Plan, for a case. Returns the six elements required by 21 CFR 312.23(a)(3)(iv), each marked PRESENT or MISSING, plus any planned studies described. Use for questions about the development plan, first-year studies, enrolment numbers, or anticipated risks.",
    input_schema: {
      type: "object",
      properties: { case_id: { type: "string" } },
      required: ["case_id"],
    },
  },
  {
    name: "draft_cover_letter",
    description:
      "Draft the IND cover letter for a case. The draft is generated from an approved fact whitelist and is automatically checked afterwards for any statement not supported by the source data. Returns the letter plus that grounding report.",
    input_schema: {
      type: "object",
      properties: { case_id: { type: "string" } },
      required: ["case_id"],
    },
  },
];

// Which output consumed a supplied field. Mirrors destinationOf() in public/app.js
// so the assistant and the input view always say the same thing.
function destinationOf(c: Any, path: string): string {
  const f = c.form_1571.fields.find((x: Any) => x.canonical_path === path);
  if (f) return f.box ? `Form 1571, Box ${f.box}` : "Form 1571, supporting data (not a numbered box)";
  if (path.startsWith("plan.")) return "1.20 General Investigational Plan";
  if (path.startsWith("investigator.")) return "Form FDA 1572 — no generator, so nothing consumes it";
  return "not used by any current output";
}

export function runTool(name: string, input: Any): { result: Any; canvas?: Any } {
  switch (name) {
    case "list_cases": {
      return { result: { cases: caseList() }, canvas: { view: "cases" } };
    }

    case "get_source_input": {
      const c = caseOr404(input.case_id);
      const contested = new Set((c.canonical.conflicts || []).map((x: Any) => x.field));
      return {
        result: {
          case_id: c.case_id,
          note: "Already-extracted structured records. Extraction from real PDF/DOCX is not built.",
          records: c.source_records.map((r: Any) => ({
            record_id: r.record_id,
            record_type: r.record_type,
            title: r.title,
            supplied: Object.entries(r.fields).map(([path, value]) => ({
              path,
              value,
              // Stated, never inferred: quoting a box number from memory is how a
              // wrong one ends up in an answer.
              destination: destinationOf(c, path),
              contested: contested.has(path),
            })),
            planned_studies: (r.planned_studies || []).length,
          })),
          contested_paths: [...contested],
        },
        canvas: { view: "input", case_id: c.case_id },
      };
    }

    case "load_case": {
      const c = caseOr404(input.case_id);
      return {
        result: {
          case_id: c.case_id,
          label: c.case_label,
          scenario_type: c.scenario_type,
          note: "All values are fictional synthetic data.",
          canonical: scalars(c.canonical),
          conflicts: (c.canonical.conflicts || []).map((x: Any) => ({
            field: x.field,
            competing_values: x.values.map((v: Any) => ({ value: v.value, from_record: v.record_id })),
          })),
          source_records: c.source_records.map((r: Any) => ({
            record_id: r.record_id,
            record_type: r.record_type,
            fields_supplied: Object.keys(r.fields).length,
          })),
          validation_summary: c.validation.summary,
        },
        canvas: { view: "form_1571", case_id: c.case_id },
      };
    }

    case "get_form_1571": {
      const c = caseOr404(input.case_id);
      const fields = c.form_1571.fields.map((f: Any) => ({
        box: f.box,
        label: f.label,
        status: f.status,
        value: f.value,
        sources: (f.provenance?.sources || []).map((s: Any) => s.record_id),
      }));
      return {
        result: { case_id: c.case_id, form: "FDA Form 1571 (POC field view)", fields },
        canvas: { view: "form_1571", case_id: c.case_id },
      };
    }

    case "get_provenance": {
      const c = caseOr404(input.case_id);
      const path = String(input.field_path || "").trim();
      const prov = c.canonical.provenance?.[path];
      if (!prov) {
        return {
          result: {
            field: path,
            error: `"${path}" is not a canonical field. Valid paths look like sponsor.legal_name, product.code_name, protocol.protocol_number, submission.submission_date.`,
          },
        };
      }
      const conflict = (c.canonical.conflicts || []).find((x: Any) => x.field === path);
      const formField = c.form_1571.fields.find((f: Any) => f.canonical_path === path);
      return {
        result: {
          case_id: c.case_id,
          field: path,
          form_1571_box: formField?.box ?? null,
          status: formField?.status ?? (conflict ? "CONFLICT" : prov.value ? "PASS" : "MISSING"),
          value: prov.value,
          supplied_by: (prov.sources || []).map((s: Any) => ({ record_id: s.record_id, source_field: s.field })),
          competing_values: conflict
            ? conflict.values.map((v: Any) => ({ value: v.value, from_record: v.record_id }))
            : undefined,
          resolution: conflict
            ? "Unresolved. The system does not select between conflicting sources."
            : undefined,
        },
        canvas: { view: "form_1571", case_id: c.case_id, focus_field: path },
      };
    }

    case "get_validation": {
      const c = caseOr404(input.case_id);
      const issues = dedupeIssues(c.validation.issues);
      const blocking = issues.filter((i) => i.status === "MISSING" || i.status === "CONFLICT");
      const warnings = issues.filter((i) => i.status === "WARNING");
      return {
        result: {
          case_id: c.case_id,
          verdict: blocking.length
            ? `NOT READY - ${blocking.length} blocking issue(s)`
            : "No blocking issues within the checks this demo performs",
          blocking: blocking.map((i) => ({ status: i.status, field: i.field, message: i.message })),
          warnings: warnings.map((i) => ({ field: i.field, message: i.message })),
          checks_passed: issues.filter((i) => i.status === "PASS").length,
          scope_note:
            "These checks cover field presence, source conflicts, and cross-document consistency only. They are not a regulatory completeness review.",
        },
        canvas: { view: "validation", case_id: c.case_id },
      };
    }

    case "get_module1_toc": {
      const c = caseOr404(input.case_id);
      const leaves = c.toc.sections.flatMap((s: Any) => s.children);
      return {
        result: {
          case_id: c.case_id,
          summary: c.toc.summary,
          outstanding: leaves
            .filter((l: Any) => l.status === "ABSENT")
            .map((l: Any) => ({ section: `${l.number} ${l.title}`, why: l.detail })),
          needs_decision: leaves
            .filter((l: Any) => l.status === "NEEDS DECISION")
            .map((l: Any) => ({ section: `${l.number} ${l.title}`, condition: l.detail })),
          present: leaves
            .filter((l: Any) => l.status === "PRESENT")
            .map((l: Any) => `${l.number} ${l.title}`),
          note: c.toc.note,
        },
        canvas: { view: "toc", case_id: c.case_id },
      };
    }

    case "get_investigational_plan": {
      const c = caseOr404(input.case_id);
      const plan = c.investigational_plan;
      return {
        result: {
          case_id: c.case_id,
          supplied: plan.supplied,
          summary: plan.summary,
          elements: plan.elements.map((e: Any) => ({
            heading: e.heading,
            status: e.status,
            value: e.value,
          })),
          planned_studies: plan.planned_studies,
          note: plan.note,
        },
        canvas: { view: "plan", case_id: c.case_id },
      };
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

export function getCase(caseId: string): Any {
  return caseOr404(caseId);
}

export function caseList(): Any[] {
  return ORDER.map((id) => ({
    case_id: id,
    label: CASES[id].case_label,
    scenario_type: CASES[id].scenario_type,
    validation: CASES[id].validation.summary,
  }));
}

export function casePayload(caseId: string): Any {
  const c = caseOr404(caseId);
  return {
    case_id: c.case_id,
    label: c.case_label,
    scenario_type: c.scenario_type,
    source_records: c.source_records,
    form_1571: c.form_1571.fields,
    toc: c.toc,
    investigational_plan: c.investigational_plan,
    validation: { summary: c.validation.summary, issues: dedupeIssues(c.validation.issues) },
    conflicts: c.canonical.conflicts || [],
  };
}

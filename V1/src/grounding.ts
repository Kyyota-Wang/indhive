// Text-level grounding check for generated prose.
//
// The pipeline can prove a field's provenance, but once a language model writes
// a paragraph, provenance stops at the input boundary. This checks the other
// end: it reads the produced text and asks whether every specific-looking claim
// in it traces back to an approved fact.
//
// Omitting an approved fact is allowed. Stating something that is not an
// approved fact is not.

type Fact = { path: string; value: any };

const norm = (s: string) => s.toLowerCase().replace(/\s+/g, " ").trim();

const MONTHS = [
  "january", "february", "march", "april", "may", "june",
  "july", "august", "september", "october", "november", "december",
];

// A model asked for "2026-08-18" will often write "August 18, 2026". That is a
// reformat of an approved fact, not an invention, so treat these as the same.
function dateVariants(iso: string): string[] {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (!m) return [iso];
  const [, y, mo, d] = m;
  const month = MONTHS[Number(mo) - 1];
  const day = String(Number(d));
  return [
    iso,
    `${month} ${day}, ${y}`,
    `${month} ${d}, ${y}`,
    `${day} ${month} ${y}`,
    `${mo}/${d}/${y}`,
    `${Number(mo)}/${day}/${y}`,
  ];
}

function factStrings(facts: Fact[]): string[] {
  const out: string[] = [];
  for (const f of facts) {
    const v = f.value;
    if (v === null || v === undefined) continue;
    const s = String(v);
    if (!s.trim()) continue;
    if (/^\d{4}-\d{2}-\d{2}$/.test(s.trim())) out.push(...dateVariants(s));
    else out.push(s);
  }
  return out;
}

const EXTRACTORS: { kind: string; re: RegExp }[] = [
  { kind: "email address", re: /[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g },
  { kind: "phone number", re: /\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b/g },
  { kind: "date", re: /\b\d{4}-\d{2}-\d{2}\b/g },
  {
    kind: "date",
    re: new RegExp(`\\b(?:${MONTHS.join("|")})\\s+\\d{1,2},?\\s+\\d{4}\\b`, "gi"),
  },
  { kind: "postal code", re: /\b\d{5}(?:-\d{4})?\b/g },
];

export type Grounding = {
  status: "clean" | "flagged";
  facts_total: number;
  facts_present: number;
  facts_omitted: string[];
  unsupported: { text: string; kind: string }[];
  note: string;
};

export function checkGrounding(text: string, facts: Fact[]): Grounding {
  const haystack = norm(text);
  const approved = factStrings(facts);
  const approvedNorm = approved.map(norm);
  const approvedBlob = approvedNorm.join(" || ");

  const present: string[] = [];
  const omitted: string[] = [];
  for (const f of facts) {
    const s = String(f.value ?? "");
    if (!s.trim()) continue;
    const variants = /^\d{4}-\d{2}-\d{2}$/.test(s.trim()) ? dateVariants(s) : [s];
    if (variants.some((v) => haystack.includes(norm(v)))) present.push(f.path);
    else omitted.push(f.path);
  }

  const seen = new Set<string>();
  const unsupported: { text: string; kind: string }[] = [];
  for (const { kind, re } of EXTRACTORS) {
    for (const match of text.matchAll(re)) {
      const raw = match[0];
      const key = norm(raw);
      if (seen.has(key)) continue;
      seen.add(key);
      if (approvedBlob.includes(key)) continue;
      // A postal code that is part of an approved phone number or address line
      // will already have matched above; anything left is genuinely unaccounted for.
      unsupported.push({ text: raw, kind });
    }
  }

  return {
    status: unsupported.length ? "flagged" : "clean",
    facts_total: facts.length,
    facts_present: present.length,
    facts_omitted: omitted,
    unsupported,
    note: unsupported.length
      ? "The draft contains specific values that do not appear in the approved source facts. Treat them as unverified."
      : "Every specific value in the draft traces back to an approved source fact.",
  };
}

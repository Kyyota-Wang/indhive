"""Module 2 — Common Technical Document Summaries.

This is the module the sponsor's package does not contain in CTD form. The
nonclinical development plan carries its own M2.4 and M2.6 sections, but under
non-standard numbering; those are rewritten here against the standard headings,
with the divergence recorded in a comment.
"""
from __future__ import annotations

from .common import (DRUG, PROTOCOL, SPONSOR, assume, cited, filed, gap, h,
                    note, pagebreak, table, table_source, trace)


def build_m2(doc):
    h(doc, 1, "Module 2 — Common Technical Document Summaries")

    # ------------------------------------------------------------------ 2.1
    h(doc, 2, "2.1 CTD Table of Contents")
    table(doc,
          ["Section", "Title", "Status in this application"],
          [["2.2", "Introduction", "Provided"],
           ["2.3", "Quality Overall Summary", "Provided"],
           ["2.4", "Nonclinical Overview", "Provided"],
           ["2.5", "Clinical Overview", "Not applicable — no clinical experience (GAP-07)"],
           ["2.6", "Nonclinical Written and Tabulated Summaries", "Provided"],
           ["2.7", "Clinical Summary", "Not applicable — no clinical experience (GAP-07)"],
           ["3", "Quality", "Provided"],
           ["4", "Nonclinical Study Reports", "Provided"],
           ["5", "Clinical Study Reports", "None — study not started (GAP-07)"]],
          widths=[0.8, 3.2, 2.3])

    # ------------------------------------------------------------------ 2.2
    h(doc, 2, "2.2 Introduction")
    cited(doc,
          f"{DRUG} is a recombinant humanised bispecific T-cell engager of approximately 55 kDa. It is "
          "a single-chain (scFv)₂ construct without an Fc domain, comprising an anti-PRAME T-cell "
          "receptor mimic arm and an anti-CD3ε arm joined by a (G4S)₃ linker and carrying a C-terminal "
          "hexahistidine C-tag. The pharmacological class is bispecific T-cell engager.",
          "12 Section A.2")
    cited(doc,
          "The proposed clinical indication is locally advanced or metastatic solid tumours that are "
          "PRAME-positive and HLA-A*02:01-positive, after at least one prior line of standard therapy. "
          "The drug product is a sterile solution for intravenous administration, 1.0 mg in 1.1 mL per "
          "single-use vial.",
          "12 Section A.2; 07_CMC 3.2.P.1")
    cited(doc,
          f"This application supports Protocol {PROTOCOL}, a Phase 1 first-in-human, multi-centre, "
          "open-label, single-agent dose-escalation and expansion study. No clinical data exist for "
          f"{DRUG}.",
          "12 Section B.3")

    pagebreak(doc)

    # ------------------------------------------------------------------ 2.3
    h(doc, 2, "2.3 Quality Overall Summary")

    h(doc, 3, "2.3.S Drug Substance")
    cited(doc,
          "The drug substance is a recombinant humanised bispecific single-chain antibody construct "
          "expressed as a (scFv)₂ of approximately 55 kDa. The domain order is (VH–VL) anti-PRAME-TCRm "
          "— (G4S)₃ — (VL–VH) anti-CD3ε, with a C-terminal His₆ C-tag used for purification and "
          "analytical identity.",
          "07_CMC 3.2.S.1.2; 12 Section A.2")
    cited(doc,
          "No International Nonproprietary Name has been assigned; an INN request is pending, and the "
          "substance is designated by its code throughout.",
          "07_CMC 3.2.S.1.1 — GAP-03")
    cited(doc,
          "Manufacture, control of materials, control of critical steps, characterisation and impurity "
          "profiling are described in Module 3 at sections 3.2.S.2 through 3.2.S.4. The clinical drug "
          "substance lot is PMX-103-DS-25-017; the lot used for toxicology is PMX-103-DS-25-014.",
          "07_CMC 3.2.S.2–3.2.S.4; 14 Invariants")
    assume(doc,
           "The toxicology lot and the clinical lot are treated as representative of the same process, "
           "so the nonclinical safety package supports the clinical material.",
           "07_CMC 3.2.S.4.4",
           assumption=(
               "Assumption: PMX-103-DS-25-014 (toxicology) and PMX-103-DS-25-017 (clinical) are comparable. "
               "The CMC dossier reports both lots but the input brief does not state that a formal "
               "comparability exercise was performed. If the two lots differ in process, scale or site, a "
               "comparability assessment under ICH Q5E is needed to bridge the nonclinical package to the "
               "clinical material, and this paragraph must be replaced."),
           anchor="representative of the same process")

    h(doc, 3, "2.3.P Drug Product")
    cited(doc,
          "The drug product is a sterile solution for intravenous infusion presented in a 2 mL Type I "
          "glass vial with a 13 mm butyl stopper and flip-off seal, filled at 1.0 mg in 1.1 mL, stored "
          "at 2–8 °C and protected from light. The clinical drug product lot is PMX-103-DP-26-007.",
          "12 Section D.6; 07_CMC 3.2.P.1, 3.2.P.5.4")

    h(doc, 3, "2.3.P.5 Control of Drug Product")
    doc.add_paragraph("The proposed release specification is reproduced below.")
    table(doc,
          ["Attribute", "Acceptance criterion", "Method"],
          [["Appearance",
            "Clear to slightly opalescent, colourless to pale yellow; essentially free of visible particles",
            "Visual inspection"],
           ["Identity", "Bands at ~55 kDa non-reduced; LC-MS peptide map match", "SDS-PAGE + LC-MS"],
           ["Purity", "≥ 95% monomer by SEC-HPLC; LMW and HMW each ≤ 5%", "TSKgel G3000SWXL"],
           ["Potency", "Cell-lysis EC50 within 0.5–2.0× of reference standard", "Luciferase cytotoxicity, 4 h"],
           ["Endotoxin", "≤ 0.25 EU/mg (≤ 0.25 EU/vial)", "LAL kinetic chromogenic"],
           ["Sterility", "No growth at 14 days", "USP <71>"],
           ["Container", "2 mL Type I glass, 13 mm butyl stopper, flip-off seal", "—"],
           ["Fill / strength", "1.0 mg / 1.1 mL", "—"],
           ["Storage", "2–8 °C, light-protected; single-use vial", "—"]],
          widths=[1.4, 3.4, 1.5])
    table_source(doc, "12 Section D.6; 07_CMC 3.2.P.5.1")

    gap(doc,
        "Batch analysis results are illustrative rather than actual.",
        "The specification above is a proposed acceptance table. The input package states that the batch "
        "values in the CMC dossier are illustrative and that actual certificates of analysis have not "
        "been issued, so no release data can be summarised against the specification.",
        "Are certificates of analysis available for lots PMX-103-DS-25-017 and PMX-103-DP-26-007? "
        "Release data for the clinical lot are required before the material may be administered.",
        "CMC (Dr. Kim)", "GAP-08")

    h(doc, 3, "2.3.P.8 Stability")
    filed(doc, "Stability summary, protocol and data",
          "Module 3, sections 3.2.S.7 and 3.2.P.7",
          "The input brief does not extract stability conclusions, so no shelf-life statement is made here.")
    trace("M2.3", "Quality overall summary", "07_CMC 3.2.S / 3.2.P; 12 D.6", "Authored, 1 assumption, GAP-08")

    pagebreak(doc)

    # ------------------------------------------------------------------ 2.4
    h(doc, 2, "2.4 Nonclinical Overview")
    note(doc,
         "The sponsor's nonclinical development plan (09_NCD) contains its own M2.4 and M2.6 sections. "
         "This overview has been written independently from the underlying data rather than transcribed, "
         "at the sponsor's instruction; see the comment on the heading below.")
    p = doc.add_paragraph()
    anchor_run = p.add_run("This overview is a fresh synthesis of the nonclinical data package.")
    doc.add_comment(
        runs=[anchor_run],
        text=("Note on scope: 13_IND_Drafting_Instructions §3 directs that 09_NCD and 11_TOX be filed "
              "as-is and not rewritten. The sponsor has instead instructed that Modules 2, 3 and 4 be "
              "authored afresh from the underlying data. This section therefore departs from the drafting "
              "instructions deliberately. The source dossiers remain the controlling documents; where this "
              "synthesis and 09_NCD differ in wording, 09_NCD governs."),
        author="IRIS", initials="IR")

    h(doc, 3, "2.4.1 Overview of the Nonclinical Testing Strategy")
    cited(doc,
          "PMX-103 does not bind the murine orthologue of the target, and its pharmacology depends on "
          "presentation of a human peptide on human HLA-A*02:01. Species selection therefore rested on "
          "two pharmacologically relevant systems: the HHD-DR1 HLA-A2.1 transgenic mouse, in which the "
          "human restriction element is present, and the cynomolgus monkey, which is cross-reactive at "
          "the CD3ε arm. Wild-type mice were used only to characterise passive disposition.",
          "11_TOX 4.2.3.1; 12 Section D.4")
    cited(doc,
          "The programme comprises in vitro potency and cytokine characterisation, in vivo "
          "dose-range-finding and anti-tumour studies, single- and repeat-dose toxicology in both "
          "species with a 28-day recovery period, a GLP repeat-dose study in the transgenic mouse, and "
          "a safety pharmacology battery covering cardiovascular, respiratory and central nervous "
          "system endpoints.",
          "12 Sections D.4, D.5; 11_TOX 4.2")

    h(doc, 3, "2.4.2 Pharmacology")
    cited(doc,
          "PMX-103 mediates redirected lysis of PRAME-positive, HLA-A*02:01-positive tumour cells with "
          "a half-maximal effective concentration of 0.62 ng/mL and a ten-percent effective "
          "concentration of 0.12 ng/mL in a four-hour calcein-release assay using A375-MA1 targets and "
          "human peripheral blood mononuclear cells.",
          "12 Section D.2 (PMX-103-IVT-002)")
    cited(doc,
          "Cytokine release accompanies target engagement, with half-maximal concentrations of 0.91, "
          "0.78 and 1.2 ng/mL for interferon-γ, tumour necrosis factor-α and interleukin-2 "
          "respectively, and a whole-blood interleukin-6 peak at 1.4 ng/mL. T-cell activation measured "
          "by CD69 and proliferation measured by CFSE dilution occur at 0.55 and 0.84 ng/mL.",
          "12 Section D.2 (PMX-103-IVT-003, IVT-004, IVT-008)")
    cited(doc,
          "Binding affinities determined by surface plasmon resonance are 3.4 nM for the anti-PRAME arm "
          "and 8.7 nM for the anti-CD3ε arm.",
          "12 Section D.2 (PMX-103-IVT-001)")
    cited(doc,
          "In vivo, complete regression of PRAME-positive xenografts was achieved in all animals at "
          "10 μg/kg in the HHD-DR1 mouse.",
          "12 Section D.4 (PMX-103-TOX-003)")

    h(doc, 3, "2.4.3 Pharmacokinetics")
    cited(doc,
          "In cynomolgus monkeys given 40 μg/kg intravenously, maximum plasma concentration was "
          "34.2 ng/mL with an area under the curve to 168 hours of 1281 ng·h/mL, clearance of "
          "31.2 mL/h/kg, volume of distribution at steady state of 3.84 L/kg, and biphasic disposition "
          "with alpha and beta half-lives of 3.1 and 96.4 hours. Subcutaneous bioavailability was "
          "71.2 percent.",
          "12 Section D.3")
    cited(doc,
          "Allometric scaling projects human clearance of 0.21 mL/h/kg and steady-state volume of "
          "0.18 L/kg. At the proposed 0.5 μg flat starting dose this gives a projected maximum "
          "concentration of 0.041 ng/mL and an area under the curve of 1.6 ng·h/mL, with alpha and beta "
          "half-lives of 2.8 and 78.2 hours.",
          "12 Section D.3")

    h(doc, 3, "2.4.4 Toxicology")
    cited(doc,
          "The no-observed-adverse-effect level is 5.0 μg/kg in the cynomolgus monkey and 10.0 μg/kg in "
          "the GLP transgenic mouse study. The maximum tolerated dose in the mouse is 30.0 μg/kg and "
          "the highest non-severely toxic dose in the monkey is 50.0 μg/kg.",
          "12 Section D.7")
    cited(doc,
          "Findings across species are consistent with on-target, cytokine-driven pharmacology rather "
          "than intrinsic organ toxicity: transient lymphopenia with T-cell redistribution, an "
          "interferon-γ and tumour necrosis factor-α peak at one to four hours resolving by day three, "
          "reversible alanine aminotransferase elevation confined to the highest doses, and reversible "
          "neuroinflammation-like signs in three of eight monkeys at 50 μg/kg. One death in eight mice "
          "occurred at 100 μg/kg and was attributed to cytokine release.",
          "12 Section D.4")
    cited(doc,
          "Safety pharmacology showed no QTcF prolongation beyond 10 ms, with a maximum change of "
          "9.2 ms and a transient 18 percent heart-rate increase at 50 μg/kg; no respiratory effects; "
          "and no abnormal Irwin findings other than mild lethargy at and above 50 μg/kg resolving by "
          "day two.",
          "12 Sections D.5, D.7")
    cited(doc,
          "Anti-drug antibodies were detected in two of eight cynomolgus monkeys at day 28.",
          "12 Section D.4 (PMX-103-TOX-005)")
    assume(doc,
           "Genotoxicity, carcinogenicity and reproductive toxicity studies have not been conducted, "
           "consistent with ICH S6(R1) and ICH S9 for a biologic in advanced cancer.",
           "11_TOX 4.2.3.7, 4.2.3.8; ICH S9",
           assumption=(
               "Assumption: the absence of genotoxicity, carcinogenicity and reproductive toxicity studies "
               "is intentional and justified under ICH S6(R1) and ICH S9, which do not expect them for a "
               "protein therapeutic in advanced malignancy. The toxicology dossier has headings for these "
               "sections; the input brief does not state their conclusions. If those sections contain "
               "anything other than a justification for not conducting the studies, this paragraph is wrong."),
           anchor="have not been conducted")

    h(doc, 3, "2.4.5 Integrated Overview and Starting Dose Justification")
    cited(doc,
          "The proposed starting dose of 0.5 μg flat was derived by a modified minimum anticipated "
          "biological effect level approach anchored on the in vitro ten-percent effective "
          "concentration of 0.12 ng/mL and the in vivo MABEL anchor of 1.0 μg/kg in the transgenic "
          "mouse.",
          "12 Sections D.2, D.7; 09_NCD M2.6.5")
    cited(doc,
          "At 0.5 μg flat, approximately 0.0075 μg/kg in a 70 kg subject, the projected maximum "
          "concentration of 0.041 ng/mL sits below the in vitro EC10 of 0.12 ng/mL, and roughly "
          "670-fold below the cynomolgus no-observed-adverse-effect level of 5.0 μg/kg on a body-weight "
          "basis.",
          "12 Sections D.3, D.7")
    assume(doc,
           "The margin to the cynomolgus NOAEL is expressed on a body-weight basis rather than on "
           "exposure, because a matched exposure at the NOAEL dose is not reported in the input package.",
           "12 Sections D.3, D.7",
           assumption=(
               "Assumption: the safety margin is stated as a dose ratio. The package reports cynomolgus PK "
               "at 40 μg/kg but not at the 5.0 μg/kg NOAEL, so an exposure-based margin cannot be computed "
               "from the data supplied. An exposure margin is the stronger justification and FDA will "
               "normally expect one; if AUC at the NOAEL is available it should replace this."),
           anchor="on a body-weight basis rather than on exposure")
    cited(doc,
          "Mandatory step-up priming at 0.5 μg on Cycle 1 Day 1 and 5 μg on Cycle 1 Day 8, with "
          "premedication and protocol-defined monitoring, is intended to mitigate cytokine release "
          "syndrome before the assigned cohort dose is given.",
          "12 Section B.3; 14 Invariants")
    trace("M2.4", "Nonclinical overview", "09_NCD; 11_TOX; 12 D.2–D.7", "Authored, 2 assumptions")

    pagebreak(doc)

    # ------------------------------------------------------------------ 2.5
    h(doc, 2, "2.5 Clinical Overview")
    gap(doc,
        "A clinical overview cannot be written.",
        f"{DRUG} has never been administered to a human subject. Protocol {PROTOCOL} has not started "
        "and no clinical data of any kind exist. A clinical overview summarises clinical pharmacology, "
        "efficacy and safety from completed studies; there is nothing to summarise.",
        "None — this is expected for an original IND with no prior human exposure. The sponsor should "
        "confirm that no investigator-initiated or foreign exposure to PMX-103 has occurred that would "
        "need to be reported here.",
        "Clinical", "GAP-07")
    doc.add_paragraph()
    cited(doc,
          "Class precedent in humans is described in the Investigator's Brochure and summarised in "
          "M1.20: the Pr20 T-cell receptor mimic antibody against the same PRAME/HLA-A*02:01 complex, "
          "the IMA402 T-cell engaging receptor, and the IMA203 PRAME TCR-T product. None of these is "
          "PMX-103 and none supports a clinical safety conclusion for this molecule.",
          "12 Section B.9; 08_IB §6")
    trace("M2.5", "Clinical overview", "GAP-07", "Not applicable")

    # ------------------------------------------------------------------ 2.6
    pagebreak(doc)
    h(doc, 2, "2.6 Nonclinical Written and Tabulated Summaries")
    note(doc,
         "Standard CTD numbering is used below. The sponsor's nonclinical development plan numbers its "
         "sections M2.6.2 pharmacology written, M2.6.3 pharmacokinetics written, M2.6.4 toxicology "
         "written, M2.6.5 integrated overview and M2.6.6 toxicology tabulated. Under ICH M4S, 2.6.3 is "
         "the pharmacology tabulated summary and the pharmacokinetics written summary is 2.6.4. The "
         "renumbering is applied here and flagged for the sponsor.")

    h(doc, 3, "2.6.1 Introduction")
    cited(doc,
          "The nonclinical package comprises in vitro pharmacology, in vivo pharmacology and "
          "dose-range-finding, pharmacokinetics in mouse and cynomolgus monkey with a human projection, "
          "single- and repeat-dose toxicology in both species including one GLP study, and a safety "
          "pharmacology battery.",
          "11_TOX 4.2; 09_NCD")

    h(doc, 3, "2.6.2 Pharmacology Written Summary")
    cited(doc,
          "Primary pharmacology is the redirected lysis of PRAME-positive, HLA-A*02:01-positive tumour "
          "cells by polyclonal T cells. Potency, cytokine release and T-cell activation parameters are "
          "tabulated in 2.6.3. Secondary pharmacology screening did not identify off-target binding of "
          "concern.",
          "11_TOX 4.2.1.1, 4.2.1.2; 12 Section D.2")

    h(doc, 3, "2.6.3 Pharmacology Tabulated Summary")
    table(doc,
          ["Assay", "Value", "Unit", "Study"],
          [["A375-MA1 PRAME/HLA-A2⁺ × human PBMC, calcein-AM 4 h — EC50", "0.62", "ng/mL", "PMX-103-IVT-002"],
           ["A375-MA1 specific lysis — EC10", "0.12", "ng/mL", "PMX-103-IVT-002"],
           ["Interferon-γ release, 24 h", "0.91", "ng/mL", "PMX-103-IVT-003"],
           ["Tumour necrosis factor-α release", "0.78", "ng/mL", "PMX-103-IVT-003"],
           ["Interleukin-2 release", "1.2", "ng/mL", "PMX-103-IVT-003"],
           ["CD69 mean fluorescence intensity, T-cell activation", "0.55", "ng/mL", "PMX-103-IVT-004"],
           ["T-cell proliferation, CFSE 72 h", "0.84", "ng/mL", "PMX-103-IVT-004"],
           ["Interleukin-6, whole blood + PBMC peak", "1.4", "ng/mL", "PMX-103-IVT-008"],
           ["Anti-PRAME K_D, Biacore", "3.4", "nM", "PMX-103-IVT-001"],
           ["Anti-CD3ε K_D, Biacore", "8.7", "nM", "PMX-103-IVT-001"]],
          widths=[3.1, 0.7, 0.7, 1.8])
    table_source(doc, "12 Section D.2; 09_NCD M2.6.2; 08_IB §5.1")

    h(doc, 3, "2.6.4 Pharmacokinetics Written Summary")
    cited(doc,
          "Disposition in the cynomolgus monkey is biphasic with a terminal half-life near four days, "
          "consistent with a non-Fc construct cleared largely by catabolism. Human parameters were "
          "projected by allometric scaling. Toxicokinetic sampling accompanied the repeat-dose studies "
          "and anti-drug antibody incidence was monitored to day 28.",
          "11_TOX 4.2.2.3–4.2.2.5; 12 Section D.3")

    h(doc, 3, "2.6.5 Pharmacokinetics Tabulated Summary")
    table(doc,
          ["Parameter", "Cynomolgus, 40 μg/kg i.v.", "Human projection, 0.5 μg flat"],
          [["Cmax (ng/mL)", "34.2", "0.041"],
           ["AUC₀₋₁₆₈ₕ (ng·h/mL)", "1281", "1.6"],
           ["Clearance (mL/h/kg)", "31.2", "0.21"],
           ["Vss (L/kg)", "3.84", "0.18"],
           ["t½ α (h)", "3.1", "2.8"],
           ["t½ β (h)", "96.4", "78.2"],
           ["Subcutaneous bioavailability (%)", "71.2", "not applicable"]],
          widths=[2.2, 2.1, 2.1])
    table_source(doc, "12 Section D.3; 09_NCD M2.6.3; 08_IB §5.2")

    h(doc, 3, "2.6.6 Toxicology Written Summary")
    cited(doc,
          "Six toxicology studies were conducted. In wild-type mice, which lack the human restriction "
          "element, a single intravenous dose up to 5000 μg/kg produced no pharmacology and served only "
          "to characterise passive disposition. In HLA-A2.1 transgenic mice, single doses up to "
          "100 μg/kg produced transient lymphopenia at 24 hours with a cytokine peak at one to four "
          "hours resolving by day three.",
          "12 Section D.4 (PMX-103-TOX-001, TOX-002)")
    cited(doc,
          "Repeat dosing every three days for four doses in the transgenic mouse produced one death in "
          "eight animals at 100 μg/kg attributed to cytokine release, and reversible alanine "
          "aminotransferase elevation at the same dose; complete regression of PRAME-positive "
          "xenografts occurred at 10 μg/kg. The GLP repeat-dose study in the same model reproduced the "
          "reversible transaminase finding at 100 μg/kg with no chronic histopathology after 28 days of "
          "recovery.",
          "12 Section D.4 (PMX-103-TOX-003, TOX-006)")
    cited(doc,
          "In the cynomolgus monkey, single doses of 50 and 500 μg/kg produced cytokine release "
          "syndrome with fever, lethargy and a twofold alanine aminotransferase rise, with T-cell "
          "redistribution at six hours. Repeat dosing every three days for four doses with 28 days of "
          "recovery produced transient lymphopenia and reversible neuroinflammation-like signs in three "
          "of eight animals at 50 μg/kg, with anti-drug antibodies in two of eight at day 28.",
          "12 Section D.4 (PMX-103-TOX-004, TOX-005)")

    h(doc, 3, "2.6.7 Toxicology Tabulated Summary")
    table(doc,
          ["Study", "Species", "Design", "Doses (μg/kg)", "Key finding"],
          [["PMX-103-TOX-001", "Mouse C57BL/6 (wild type)", "Single i.v.", "10, 100, 1000, 5000",
            "No pharmacology; passive PK only"],
           ["PMX-103-TOX-002", "HHD-DR1 (HLA-A2.1 Tg) mouse", "Single i.v.", "0.01, 0.1, 1, 10, 100",
            "Transient lymphopenia 24 h; IFN-γ/TNF-α peak 1–4 h, resolved d3"],
           ["PMX-103-TOX-003", "HHD-DR1 mouse", "Q3D × 4", "1, 10, 30, 100",
            "1/8 death at 100 (cytokine-related); reversible ALT at 100; 100% xenograft regression at 10"],
           ["PMX-103-TOX-004", "Cynomolgus monkey", "Single i.v.", "0.5, 5, 50, 500",
            "CRS at 50/500 (fever, lethargy, ALT 2×); T-cell redistribution at 6 h"],
           ["PMX-103-TOX-005", "Cynomolgus monkey", "Q3D × 4 + 28-d recovery", "0.5, 5, 50",
            "Transient lymphopenia; reversible neuroinflammation-like signs 3/8 at 50; ADA 2/8 at d28"],
           ["PMX-103-TOX-006", "HHD-DR1 mouse (GLP)", "Q3D × 4 + 28-d recovery", "1, 10, 30, 100",
            "GLP grade; reversible ALT at 100; no chronic histopathology"]],
          widths=[1.2, 1.4, 1.2, 1.1, 2.4])
    table_source(doc, "12 Section D.4; 11_TOX 4.2.3; 09_NCD M2.6.4")

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run("Safety pharmacology").bold = True
    table(doc,
          ["Study", "System", "Design", "Finding"],
          [["PMX-103-SP-001", "Cardiovascular, telemetry", "Cynomolgus n=4, single i.v. 5 and 50 μg/kg",
            "No QTcF > 10 ms (max Δ 9.2 ms); heart rate +18% at 50, transient"],
           ["PMX-103-SP-002", "Respiratory", "Plethysmography, rat, 100 μg/kg i.v.",
            "No effect on respiratory rate or tidal volume"],
           ["PMX-103-SP-003", "Central nervous system, Irwin", "Rat, 100 μg/kg i.v.",
            "No abnormal findings; mild lethargy at ≥ 50, resolved by day 2"]],
          widths=[1.2, 1.5, 2.0, 2.6])
    table_source(doc, "12 Section D.5; 11_TOX 4.2.1.3")

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run("Key safety values").bold = True
    table(doc,
          ["Parameter", "Value", "Source study"],
          [["MABEL anchor (mouse)", "1.0 μg/kg", "PMX-103-TOX-002"],
           ["NOAEL (cynomolgus)", "5.0 μg/kg", "PMX-103-TOX-005"],
           ["NOAEL (GLP mouse)", "10.0 μg/kg", "PMX-103-TOX-006"],
           ["MTD (mouse)", "30.0 μg/kg", "PMX-103-TOX-003"],
           ["HNSTD (cynomolgus)", "50.0 μg/kg", "PMX-103-TOX-005"],
           ["QTcF maximum change (cynomolgus)", "9.2 ms", "PMX-103-SP-001"]],
          widths=[2.6, 1.4, 2.2])
    table_source(doc, "12 Section D.7; 14 Invariants sheet")
    trace("M2.6", "Nonclinical written and tabulated summaries", "12 D.2–D.7; 11_TOX; 09_NCD", "Authored")

    # ------------------------------------------------------------------ 2.7
    h(doc, 2, "2.7 Clinical Summary")
    gap(doc,
        "A clinical summary cannot be written.",
        "As for the clinical overview, no clinical data exist. There is no biopharmaceutics, clinical "
        "pharmacology, efficacy or safety content to summarise.",
        "None — expected for an original IND. See GAP-07.",
        "Clinical", "GAP-07")
    trace("M2.7", "Clinical summary", "GAP-07", "Not applicable")

    pagebreak(doc)

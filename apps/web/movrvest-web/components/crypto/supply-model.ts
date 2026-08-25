/**
 * Token supply, read as an answer rather than an evidence inventory.
 *
 * The page this replaces rendered fourteen claim cards followed by ten
 * pairwise comparison cards — HYPE's protocol maximum appeared three
 * times as claims and three more times inside corroboration cards, one
 * fact in six boxes, and four circulating readings produced six equally
 * prominent conflict cards. Every one of those facts is still here;
 * what changed is which of them the investor meets first.
 *
 * The rules this module owns:
 *
 * - **grouping is by the typed concept and nothing else.** Figures
 *   carry `concept`; comparisons now carry `leftConcept`/`rightConcept`
 *   from the domain's own `SupplyFact.concept`. No label is parsed, no
 *   source name matched, no formatted value compared.
 * - **a comparison belongs to a concept only when both sides claim
 *   it.** A `coexist` verdict is precisely the cross-concept case —
 *   *"different quantities, both able to be right"* — and assigning one
 *   to a single concept would name a winner between two quantities that
 *   are not rivals. Those go to the audit.
 * - **nothing is upgraded, chosen, ranged or totalled.** A reading is
 *   presented only where the domain's own comparisons already settled
 *   agreement; otherwise the row reads "Not settled" and says why. No
 *   provider is picked, no exclusion summed, no dilution inferred.
 * - **"Not settled" is a state, not a failure.** It is what this
 *   platform can honestly say, and it carries the reason.
 */

import type {
  SupplyComparisonView,
  SupplyFigureView,
  SupplyView,
} from "@/lib/api/crypto-dossier";

/** The domain's verdict token for two sources reporting the same
    quantity and agreeing. The other two — `conflicted` and `coexist` —
    are both reasons a figure is not settled here, for different
    reasons, and neither is ever read out of a sentence. */
const AGREEMENT = "corroborated";

/** The concepts the summary lists, in the order an investor reads
    them: what can ever exist, what exists now, what trades, what is
    still to come, and what is held aside. Concepts absent from a
    token's evidence are omitted — never rendered as an empty group. */
export const CONCEPT_ORDER = [
  "max_supply",
  "emitted_supply",
  "circulating_estimate",
  "future_emissions",
  "excluded_balance",
] as const;

/** Why a row shows no single figure. The two reasons are different
    claims and must never be worded the same way. */
export type UnsettledKind =
  //: Sources claim the same quantity and disagree.
  | "conflicted"
  //: Several distinct facts under one concept — four excluded
  //: addresses, say — which the domain never compared because they are
  //: not rivals. Not a disagreement, and not unsettled.
  | "several"
  //: A figure is shown.
  | null;

export interface SupplyRow {
  concept: string;
  /** The quantity's name, in the backend's own words. */
  label: string;
  /** The figure, where the evidence permits presenting one — otherwise
      null, which renders as "Not settled". */
  stated: string | null;
  /** The standing, in plain investor language. */
  status: string;
  /** One short sentence: why it reads as it does. */
  because: string;
  /** How many source claims stand behind the row. */
  sourceCount: number;
  /** Null where a figure is shown; otherwise why there is none. */
  unsettledKind: UnsettledKind;
}

export interface SupplyGroup {
  concept: string;
  label: string;
  figures: readonly SupplyFigureView[];
  /** Comparisons whose two sides both claim this concept. */
  comparisons: readonly SupplyComparisonView[];
}

export interface SupplyModel {
  /** Section 1 — what MOVRvest can say. */
  rows: readonly SupplyRow[];
  /** Section 2 — what remains unsettled. */
  unsettled: readonly { stated: string; consequence: string }[];
  /** Section 3 — source detail, grouped by concept. */
  groups: readonly SupplyGroup[];
  /** Section 4 — every comparison, including the cross-concept ones. */
  audit: readonly SupplyComparisonView[];
  /** The backend's own sentence where nothing is held at all. */
  unavailableBecause: string | null;
}

function figuresOf(
  supply: SupplyView,
  concept: string,
): readonly SupplyFigureView[] {
  return supply.figures.filter((figure) => figure.concept === concept);
}

/** Comparisons both of whose sides claim this concept. A cross-concept
    comparison is deliberately excluded: it is about the relationship
    between two quantities, not about either one of them. */
function comparisonsOf(
  supply: SupplyView,
  concept: string,
): readonly SupplyComparisonView[] {
  return supply.comparisons.filter(
    (item) => item.leftConcept === concept && item.rightConcept === concept,
  );
}

/**
 * What may be shown for one concept, and why.
 *
 * A figure is presented only where every same-concept comparison
 * touching this quantity is a corroboration, or where a single source
 * reports it and no comparison contradicts it. The moment one conflict
 * exists, the row reads "Not settled" — this layer never chooses
 * between providers, averages them, or presents a range nobody
 * published.
 */
function rowFor(
  supply: SupplyView,
  concept: string,
): SupplyRow | null {
  const figures = figuresOf(supply, concept);

  if (figures.length === 0) {
    return null;
  }

  const comparisons = comparisonsOf(supply, concept);

  // Keyed on the domain's own verdict token, never on the display
  // sentence. The first draft of this matched `verdictStated` against
  // "corroborated" — and the backend's word for agreement is **"Agree"**,
  // so every corroboration counted as a conflict and HYPE's
  // three-source protocol maximum would have read "Not settled". That
  // is the prose-matching rule failing in the one place it is most
  // expensive.
  const conflicts = comparisons.filter(
    (item) => item.verdict !== AGREEMENT,
  );

  const label = figures[0].conceptStated;
  const sourceCount = figures.length;

  // Every same-concept comparison agrees: the sources report the same
  // quantity, so the figure they agree on may be shown. It is still a
  // provider claim — the standing sentence is the backend's, and
  // nothing here promotes it to "established" or "verified".
  if (conflicts.length === 0 && comparisons.length > 0) {
    return {
      concept,
      label,
      stated: figures[0].stated,
      status:
        sourceCount === 2
          ? "Two reports align"
          : `${sourceCount} reports align`,
      because: figures[0].standingStated,
      sourceCount,
      unsettledKind: null,
    };
  }

  // One source, nothing to disagree with it. Presented as exactly that.
  if (figures.length === 1) {
    return {
      concept,
      label,
      stated: figures[0].stated,
      status: "One report",
      because: figures[0].standingStated,
      sourceCount,
      unsettledKind: null,
    };
  }

  // **Several figures the domain never compared are not in
  // disagreement.** HYPE's four excluded balances are four *addresses*
  // reported by one source — 241.4m, 46.7m, 1,673.8 and 2.7 HYPE — and
  // `compare()` was never asked about them, because they are not rival
  // claims to one quantity. Reading "multiple figures, no agreement" as
  // a conflict manufactured a disagreement this platform never
  // observed, and then told the investor a quantity was unsettled that
  // nobody had contested. They are listed, counted and left alone: no
  // figure is promoted to represent the group, and **no total is
  // computed**, because the backend owns no total.
  if (comparisons.length === 0) {
    return {
      concept,
      label,
      stated: null,
      status: `${sourceCount} reported ${sourceCount === 1 ? "value" : "values"}`,
      because: "Listed separately below; this platform totals nothing.",
      sourceCount,
      unsettledKind: "several",
    };
  }

  // A conflict stands. No figure, and the reason is the domain's own
  // account of the disagreement rather than a summary of it.
  return {
    concept,
    label,
    stated: null,
    status: "Reported figures conflict",
    because:
      conflicts[0]?.because ??
      "Reported figures differ and this platform does not choose between them.",
    sourceCount,
    unsettledKind: "conflicted",
  };
}

/**
 * The consequence of each unsettled quantity, in this platform's terms.
 *
 * The backend's `unresolved` sentences say what is unresolved; this
 * adds what follows *for MOVRvest* — that it therefore presents no
 * single figure. It draws no investment implication, and there is
 * nowhere in this shape to put one.
 */
function unsettledFrom(
  supply: SupplyView,
  rows: readonly SupplyRow[],
): readonly { stated: string; consequence: string }[] {
  const items: { stated: string; consequence: string }[] = [];

  for (const row of rows) {
    // Only a genuine disagreement belongs here. A concept carrying
    // several uncompared facts is not unsettled, and saying so would
    // invent a controversy.
    if (row.unsettledKind === "conflicted") {
      items.push({
        stated: `${row.label} is not settled.`,
        consequence: `MOVRvest therefore does not present one ${row.label.toLowerCase()} figure.`,
      });
    }
  }

  // The backend's own unresolved sentences, kept verbatim and never
  // deduplicated against the above — they are different statements.
  for (const stated of supply.unresolved) {
    items.push({ stated, consequence: "" });
  }

  return items;
}

export function supplyModel(supply: SupplyView): SupplyModel {
  const present = CONCEPT_ORDER.filter(
    (concept) => figuresOf(supply, concept).length > 0,
  );

  const rows = present
    .map((concept) => rowFor(supply, concept))
    .filter((row): row is SupplyRow => row !== null);

  const groups: SupplyGroup[] = present.map((concept) => ({
    concept,
    label: figuresOf(supply, concept)[0].conceptStated,
    figures: figuresOf(supply, concept),
    comparisons: comparisonsOf(supply, concept),
  }));

  // Any concept the corpus carries that this module's order does not
  // name still gets a group: an unknown quantity must not vanish
  // because a constant here was written before it existed.
  for (const figure of supply.figures) {
    if (!present.includes(figure.concept as (typeof CONCEPT_ORDER)[number])) {
      if (!groups.some((group) => group.concept === figure.concept)) {
        groups.push({
          concept: figure.concept,
          label: figure.conceptStated,
          figures: figuresOf(supply, figure.concept),
          comparisons: comparisonsOf(supply, figure.concept),
        });
      }
    }
  }

  return {
    rows,
    unsettled: unsettledFrom(supply, rows),
    groups,
    // Every comparison, in served order — the same-concept ones the
    // groups also show, and the cross-concept ones only reachable here.
    audit: supply.comparisons,
    unavailableBecause: supply.unavailableBecause,
  };
}

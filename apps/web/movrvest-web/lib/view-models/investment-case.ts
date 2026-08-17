export type ConvictionLevel =
  | "Very High Conviction"
  | "High Conviction"
  | "Moderate Conviction"
  | "Low Conviction";

/**
 * One holding, as judged by the Artificial CIO.
 *
 * Price targets and upside or downside projections are absent by design: the
 * platform cannot yet evidence them, and an estimated figure on an investment
 * dashboard reads as a measurement.
 *
 * `previousDecisions` is recorded, not inferred. A holding the CIO is judging
 * for the first time reports null rather than "no change".
 */
/**
 * How far conviction moved since the last decision, and what moved under it.
 *
 * `because` is empty when no score moved and also when the earlier
 * decision predates the scores being recorded — `unexplained` tells those
 * apart, so a silence is never rendered as "nothing changed".
 */
export interface ConvictionChangeViewModel {
  previous: number;
  /** Signed, never zero. */
  delta: number;
  /** The movement as the investor reads it, worded by the backend. */
  stated: string;
  because: readonly string[];
  unexplained: boolean;
}

/** Which way a case has been moving across recorded decisions. */
export interface DecisionTrendViewModel {
  /** "stable" | "improving" | "deteriorating" — styled, never parsed. */
  direction: string;
  /** The trend as the investor reads it, worded by the backend. */
  stated: string;
}

/**
 * What the Artificial CIO asks the investor to consider.
 *
 * Not the recommendation renamed: the same judgement asks a different
 * thing of someone who already holds the security. A consideration,
 * never an instruction — MOVRvest recommends and the investor decides.
 */
export interface ExecutiveActionViewModel {
  kind: string;
  statement: string;
  because: string;
  checkpoint: string | null;
}

export interface RankedInvestmentCaseViewModel {
  rank: number;
  symbol: string;
  /** Decision state, e.g. PREPARE, INVESTIGATE, REJECT. */
  recommendation: string;
  /** Null where the CIO withheld one — never rendered as a zero. */
  conviction: number | null;
  /** Null with it: a label is a word for a number, and there is none. */
  convictionLevel: ConvictionLevel | null;
  committeeAgreement: number;
  /** This security's own safety, higher being safer. Null where its
   *  price history was too short to measure — never the same as safe. */
  safetyScore: number | null;
  summary: string;
  whyNow: readonly string[];
  risks: readonly string[];
  expectedHoldingPeriod: string;
  /** What the CIO decided about this holding before, or null if never. */
  trend: DecisionTrendViewModel | null;
  action: ExecutiveActionViewModel | null;
  convictionChange: ConvictionChangeViewModel | null;
  /** What kind of investment the CIO reads this as. Null where nothing
   *  about the security itself could be gathered. */
  playbookName: string | null;
  dossierHref: string;
}

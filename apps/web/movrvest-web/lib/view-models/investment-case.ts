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
export interface RankedInvestmentCaseViewModel {
  rank: number;
  symbol: string;
  /** Decision state, e.g. PREPARE, INVESTIGATE, REJECT. */
  recommendation: string;
  conviction: number;
  convictionLevel: ConvictionLevel;
  committeeAgreement: number;
  riskLevel: string;
  summary: string;
  whyNow: readonly string[];
  risks: readonly string[];
  expectedHoldingPeriod: string;
  /** What the CIO decided about this holding before, or null if never. */
  previousDecisions: string | null;
  dossierHref: string;
}

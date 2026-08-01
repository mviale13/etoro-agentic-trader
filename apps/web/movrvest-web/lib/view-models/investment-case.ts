export type ConvictionLevel =
  | "Very High Conviction"
  | "High Conviction"
  | "Moderate Conviction"
  | "Low Conviction";

/**
 * One holding, as judged by the Artificial CIO.
 *
 * Price targets, upside and downside projections and conviction history are
 * absent by design: the platform cannot yet evidence them, and an estimated
 * figure on an investment dashboard reads as a measurement.
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
  dossierHref: string;
}

/**
 * The opportunity pipeline, as the Artificial CIO reports it.
 *
 * Every number here was measured. Expected upside, price targets and sector
 * classification are absent because the platform cannot evidence them — an
 * estimate on an investment dashboard reads as a measurement.
 */
export interface ResearchFunnelViewModel {
  /** Watched securities the portfolio does not hold. */
  candidates: number;
  /** How many of them this cycle looked at. */
  reviewed: number;
  /** How many could be described on their own evidence. */
  evidenced: number;
  /** Reviewed but not describable, so deliberately not judged. */
  unevidenced: number;
  /** Candidates this cycle did not have the budget to look at. */
  notReviewed: number;
  judged: number;
  actionable: number;
}

export interface ResearchCandidateViewModel {
  rank: number;
  symbol: string;
  name: string;
  /** The watchlist that names it. */
  source: string;
  /** Decision state: REJECT, MONITOR, INVESTIGATE, PREPARE, RECOMMEND. */
  recommendation: string;
  conviction: number;
  /** The conviction put into words by the backend, e.g. "High Conviction". */
  convictionLabel: string;

  /** Null where the platform did not measure it. Never zero. */
  qualityScore: number | null;
  valuationScore: number | null;
  /** From this security's own volatility and deepest observed fall. */
  safetyScore: number | null;
  evidenceScore: number;

  /** Room the portfolio has for this security, under the investor's policy. */
  portfolioFitScore: number | null;

  /** How old that evidence is, e.g. "Yahoo Finance, 14 minutes ago". */
  evidenceAsOf: string | null;

  /** Evidence behind the decision, as weighed — not curated into a case. */
  evidenceWeighed: readonly string[];
  whyNotYet: string;
  missingEvidence: readonly string[];
  catalysts: readonly string[];
  nextTrigger: string | null;
  previousDecisions: string | null;

  dossierHref: string;
}

/**
 * A watched security the cycle could not judge, by name.
 *
 * The funnel counts these; this names them. A security silently absent
 * from the candidate list reads as considered-and-dismissed, which is a
 * different claim from "nobody looked" or "nothing could be read".
 */
export interface WatchedCandidateViewModel {
  symbol: string;
  name: string;
  /** The watchlist that names it. */
  source: string;
}

export interface ResearchPipelineViewModel {
  funnel: ResearchFunnelViewModel;
  candidates: readonly ResearchCandidateViewModel[];
  /** Reviewed — a request was spent — but no evidence came back. */
  unevidenced: readonly WatchedCandidateViewModel[];
  /** Outside this cycle's review budget; nobody looked. */
  notReviewed: readonly WatchedCandidateViewModel[];
}

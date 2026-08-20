export type ChangeSeverity = "information" | "attention" | "important";

export interface PortfolioSnapshotViewModel {
  totalEquity: number;
  availableCash: number | null;
  invested: number;
  /** Null when the backend does not publish a P&L figure. */
  unrealizedProfitLoss: number | null;
  openPositions: number;
  /** Null when the backend does not publish an order count. */
  pendingOrders: number | null;
  /** Cash as a share of the account, measured by the backend. */
  liquidityPct: number | null;
  healthScore: number;
  /** The backend's word for the health score, e.g. "Healthy". */
  healthLabel: string;
  /**
   * The Brain's overall risk level, or null where none could be measured.
   * Null is rendered as "Not measured", never as a reassuring default.
   */
  riskLevel: string | null;
  /** The largest holding, or null when the account holds nothing. */
  largestPositionSymbol: string | null;
  largestPositionPct: number | null;
}

export interface ExecutiveChangeViewModel {
  id: string;
  severity: ChangeSeverity;
  title: string;
  detail: string;
  context?: string;
  href?: string;
}

export type PriorityUrgency = "now" | "today" | "monitor";

export interface ExecutivePriorityViewModel {
  id: string;
  urgency: PriorityUrgency;
  title: string;
  rationale: string;
  estimatedMinutes?: number;
  href?: string;
}

/** The Artificial CIO's explanation of its current decision. */
export interface ExecutiveBriefViewModel {
  symbol: string;
  headline: string;
  summary: string;

  /**
   * How far the committees that spoke agreed.
   *
   * Null where none of them could form a view — not the same as their
   * having disagreed, and never rendered as a zero.
   */
  confidence: number | null;
}

/** One counted fact about today, worded by the backend. */
export interface BriefingLineViewModel {
  statement: string;
  /** True where the line is news, false where it is the absence of news. */
  notable: boolean;
}

/**
 * What the investor needs to know today, before anything else.
 *
 * `headline` is null on a day where nothing asks for attention. The page
 * shows that as itself — it never promotes the least uneventful fact to
 * fill the space.
 */
export interface TodayBriefingViewModel {
  lines: readonly BriefingLineViewModel[];
  headline: string | null;
  isQuiet: boolean;
}

export interface ExecutiveWorkspaceViewModel {
  lastReviewedAt: string;
  situation: "stable" | "attention" | "important";

  today: TodayBriefingViewModel;

  portfolio: PortfolioSnapshotViewModel;

  brief?: ExecutiveBriefViewModel;

  changes: readonly ExecutiveChangeViewModel[];
  priorities: readonly ExecutivePriorityViewModel[];
}

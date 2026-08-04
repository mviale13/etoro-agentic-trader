export type ChangeSeverity = "information" | "attention" | "important";

export interface PortfolioSnapshotViewModel {
  totalEquity: number;
  availableCash: number;
  invested: number;
  /** Null when the backend does not publish a P&L figure. */
  unrealizedProfitLoss: number | null;
  openPositions: number;
  /** Null when the backend does not publish an order count. */
  pendingOrders: number | null;
  healthScore: number;
  healthLabel: string;
  riskLevel: string;
  diversification: string;
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

export interface ExecutiveWorkspaceViewModel {
  lastReviewedAt: string;
  situation: "stable" | "attention" | "important";

  portfolio: PortfolioSnapshotViewModel;

  brief?: ExecutiveBriefViewModel;

  changes: readonly ExecutiveChangeViewModel[];
  priorities: readonly ExecutivePriorityViewModel[];
}

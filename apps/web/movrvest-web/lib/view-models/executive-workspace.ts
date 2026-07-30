export type ChangeSeverity = "information" | "attention" | "important";

export interface PortfolioSnapshotViewModel {
  totalEquity: number;
  availableCash: number;
  invested: number;
  unrealizedProfitLoss: number;
  openPositions: number;
  pendingOrders: number;
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

export interface ExecutiveWorkspaceViewModel {
  lastReviewedAt: string;
  situation: "stable" | "attention" | "important";

  portfolio: PortfolioSnapshotViewModel;

  changes: readonly ExecutiveChangeViewModel[];
  priorities: readonly ExecutivePriorityViewModel[];
}

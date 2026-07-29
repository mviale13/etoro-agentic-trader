export type ChangeSeverity = "information" | "attention" | "important";

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
  headline: string;
  summary: string;

  reviewed: {
    portfolioHoldings: number;
    companies: number;
    marketEvents: number;
    macroIndicators: number;
  };

  changes: readonly ExecutiveChangeViewModel[];
  priorities: readonly ExecutivePriorityViewModel[];
}

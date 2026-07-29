export type ExecutivePriority = {
  symbol: string;
  name: string;
  executiveScore: number;
  summary: string;
  rationale: string;
  href: string;
};

export type PortfolioHealthSummary = {
  grade: string;
  status: string;
  summary: string;
  riskLevel: string;
  cashAllocation: number;
};

export type MarketIntelligenceSummary = {
  headline: string;
  summary: string;
  signals: string[];
};

export type ImportantEvent = {
  title: string;
  timing: string;
  summary: string;
  href: string;
};

export type ExecutiveWorkspaceViewModel = {
  greeting: string;
  dateLabel: string;
  briefing: string;
  priorities: ExecutivePriority[];
  portfolio: PortfolioHealthSummary;
  market: MarketIntelligenceSummary;
  importantEvent?: ImportantEvent;
};

export type CommitteeView = {
  name: string;
  verdict: "Strong support" | "Support" | "Neutral" | "Caution";
};

export type EvidenceView = {
  label: string;
  value: string;
  explanation: string;
};

export type PortfolioImpactView = {
  currentAllocation: string;
  suggestedAllocation: string;
  cashRequired: string;
  policyStatus: string;
};

export type ExecutiveBriefViewModel = {
  symbol: string;
  companyName: string;
  sector: string;
  executiveScore: number;
  attentionLabel: string;
  readingTime: string;
  generatedAt: string;
  executiveSummary: string;
  whyNow: string[];
  committees: CommitteeView[];
  portfolioImpact: PortfolioImpactView;
  evidence: EvidenceView[];
  risks: string[];
  executiveAssessment: string[];
};

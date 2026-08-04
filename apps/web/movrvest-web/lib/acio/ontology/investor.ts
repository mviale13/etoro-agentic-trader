export const InvestorEvidenceKinds = {
  Preference: "investor_preference",
  Behavior: "investor_behavior",
  RiskTolerance: "risk_tolerance",
  InvestmentHorizon: "investment_horizon",
  LiquidityNeed: "liquidity_need",
  KnowledgeLevel: "knowledge_level",
  DecisionPattern: "decision_pattern",
  ConvictionPattern: "conviction_pattern",
} as const;

export type InvestorEvidenceKind =
  (typeof InvestorEvidenceKinds)[keyof typeof InvestorEvidenceKinds];

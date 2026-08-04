export const CompanyEvidenceKinds = {
  Growth: "company_growth",
  Profitability: "company_profitability",
  Valuation: "company_valuation",
  Quality: "company_quality",
  Momentum: "company_momentum",
  BalanceSheet: "company_balance_sheet",
  CashFlow: "company_cash_flow",
  CompetitivePosition: "company_competitive_position",
} as const;

export type CompanyEvidenceKind =
  (typeof CompanyEvidenceKinds)[keyof typeof CompanyEvidenceKinds];

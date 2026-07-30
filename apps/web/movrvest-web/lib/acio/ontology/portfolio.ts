export const PortfolioEvidenceKinds = {
  PortfolioValue: "portfolio_value",
  CashBalance: "cash_balance",
  CashAllocation: "cash_allocation",
  InvestedValue: "invested_value",
  PositionCount: "position_count",
  PositionConcentration: "position_concentration",
  SectorExposure: "sector_exposure",
  Drawdown: "drawdown",
  UnrealizedPnl: "unrealized_pnl",
} as const;

export type PortfolioEvidenceKind =
  (typeof PortfolioEvidenceKinds)[keyof typeof PortfolioEvidenceKinds];

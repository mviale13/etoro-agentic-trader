export const MarketEvidenceKinds = {
  Trend: "market_trend",
  Breadth: "market_breadth",
  Volatility: "market_volatility",
  Sentiment: "market_sentiment",
  Regime: "market_regime",
  SectorLeadership: "sector_leadership",
} as const;

export type MarketEvidenceKind =
  (typeof MarketEvidenceKinds)[keyof typeof MarketEvidenceKinds];

export const MacroEvidenceKinds = {
  Regime: "macro_regime",
  InterestRates: "interest_rates",
  Inflation: "inflation",
  EconomicGrowth: "economic_growth",
  Employment: "employment",
  Liquidity: "macro_liquidity",
  Currency: "currency_conditions",
} as const;

export type MacroEvidenceKind =
  (typeof MacroEvidenceKinds)[keyof typeof MacroEvidenceKinds];

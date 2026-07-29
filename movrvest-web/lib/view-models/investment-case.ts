export type ConvictionLevel =
  | "Very High Conviction"
  | "High Conviction"
  | "Moderate Conviction"
  | "Low Conviction";

export type RiskLevel = "Low" | "Moderate" | "Elevated" | "High";

export interface RankedInvestmentCaseViewModel {
  rank: 1 | 2 | 3;
  symbol: string;
  companyName: string;
  exchange: string;
  conviction: number;
  convictionLevel: ConvictionLevel;
  convictionChange: number;
  expectedUpside: number;
  potentialDownside: number;
  riskLevel: RiskLevel;
  committeeAgreement: number;
  recommendation: "Increase" | "Hold" | "Reduce";
  whyNow: readonly string[];
  summary: string;
  dossierHref: string;
}

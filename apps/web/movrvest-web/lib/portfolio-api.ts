export type Allocation = {
  cash: number;
  stocks: number;
  etfs: number;
  crypto: number;
  unclassified: number;
};

export type PortfolioResponse = {
  total_value: number;
  total_value_eur: number;
  available_cash_usd: number;
  available_cash_eur: number;
  invested_usd: number;
  invested_eur: number;
  liquidity_pct: number;
  positions: number;
  allocation: Allocation;
  risk_flags: string[];
  last_sync: string | null;
  source: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function getPortfolio(): Promise<PortfolioResponse> {
  const response = await fetch(`${API_URL}/portfolio/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load portfolio.");
  }

  return response.json();
}

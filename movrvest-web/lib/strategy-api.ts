const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export type StrategyReadiness = {
  status: "empty" | "incomplete" | "ready";
  configured: boolean;
  completed_fields: number;
  total_fields: number;
  missing_fields: string[];
  message: string;
};

export type InvestorStrategy = {
  status: string;

  strategy: {
    name: string;
    description: string;
  };

  profile: {
    name: string;
    base_currency: string;
  };

  objectives: {
    primary_goal: string;
    time_horizon_years: number | null;
    target_annual_return_pct: number | null;
    maximum_acceptable_drawdown_pct: number | null;
  };

  portfolio_policy: {
    target_cash_pct: number | null;
    minimum_cash_pct: number | null;
    maximum_single_position_pct: number | null;
    maximum_crypto_pct: number | null;
  };

  investment_preferences: {
    investor_type?: string;
    style: string[];
    preferred_assets: string[];
    excluded_assets: string[];
    allow_crypto: boolean;
    allow_leverage: boolean;
  };

  decision_rules: {
    minimum_committee_confidence_to_buy: number | null;
    require_human_approval: boolean;
    automatic_trading_enabled: boolean;
  };

  notes: string[];
};

export async function getStrategyReadiness(): Promise<StrategyReadiness> {
  const response = await fetch(
    `${API_URL}/strategy/readiness`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load strategy status.",
    );
  }

  return response.json();
}

export async function getStrategy(): Promise<InvestorStrategy> {
  const response = await fetch(
    `${API_URL}/strategy/`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load Investment Policy.",
    );
  }

  return response.json();
}

export async function updateStrategy(
  strategy: InvestorStrategy,
): Promise<InvestorStrategy> {
  const response = await fetch(
    `${API_URL}/strategy/`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(strategy),
    },
  );

  if (!response.ok) {
    throw new Error(
      "Unable to save Investment Policy.",
    );
  }

  return response.json();
}

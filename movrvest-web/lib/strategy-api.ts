const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export type StrategyReadiness = {
  configured: boolean;
  missing_fields: string[];
  message: string;
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

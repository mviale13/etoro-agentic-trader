export type PortfolioHealthResponse = {
  score: number;
  summary: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function getPortfolioHealth(): Promise<PortfolioHealthResponse> {
  const response = await fetch(`${API_URL}/portfolio-health/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load portfolio health.");
  }

  return response.json();
}
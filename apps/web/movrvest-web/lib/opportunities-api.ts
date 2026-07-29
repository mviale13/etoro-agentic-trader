export type OpportunityResponse = {
  company: string;
  action: string;
  confidence: number;
  summary: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function getOpportunities(): Promise<OpportunityResponse[]> {
  const response = await fetch(`${API_URL}/opportunities/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load top opportunities.");
  }

  return response.json();
}
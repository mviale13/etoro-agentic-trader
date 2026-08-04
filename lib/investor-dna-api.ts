export type InvestorDNAResponse = {
  understanding: number;
  message: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function getInvestorDNA(): Promise<InvestorDNAResponse> {
  const response = await fetch(`${API_URL}/investor-dna/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load Investor DNA.");
  }

  return response.json();
}
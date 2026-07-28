const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export type Insight = {
  priority: number;
  category: string;
  title: string;
  message: string;
  evidence: string[];
};

export type BrainResponse = {
  status?: string;
  summary: string;
  focus: "opportunities" | "portfolio";

  portfolio: {
    total_value: number;
    total_value_eur: number;
    positions: number;
    cash_allocation: number;
  };

  recommendation: {
    symbol: string;
    action: string;
    confidence: number;
  };

  observation: {
    title: string;
    message: string;
  };

  investor_dna: {
    confidence: number;
    message?: string;
  };

  insights: Insight[];
};

export async function getBrain(): Promise<BrainResponse> {
  const response = await fetch(
    `${API_URL}/brain/`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load the Brain.",
    );
  }

  return response.json();
}

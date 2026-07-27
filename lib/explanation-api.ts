export type ExplanationResponse = {
  recommendation: string;
  confidence: number;
  reasons: string[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export async function getExplanation(): Promise<ExplanationResponse> {
  const response = await fetch(
    `${API_URL}/explain`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Unable to load explanation.");
  }

  return response.json();
}
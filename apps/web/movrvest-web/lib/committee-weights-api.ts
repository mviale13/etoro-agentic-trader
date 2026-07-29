const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type CommitteeWeightsResponse = {
  regime: string;
  weights: Record<string, number>;
};

export async function getCommitteeWeights(): Promise<CommitteeWeightsResponse> {
  const response = await fetch(`${API_URL}/committee/weights`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load committee weights.");
  }

  return response.json();
}

export type ObservationResponse = {
  title: string;
  message: string;
  category: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function getObservation(): Promise<ObservationResponse> {
  const response = await fetch(`${API_URL}/observation/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load investor observation.");
  }

  return response.json();
}
export type ReflectionResponse = {
  title: string;
  message: string;
  source: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function getReflection(): Promise<ReflectionResponse> {
  const response = await fetch(`${API_URL}/reflection/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load daily reflection.");
  }

  return response.json();
}
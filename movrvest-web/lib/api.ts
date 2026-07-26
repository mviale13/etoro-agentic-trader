import { TodayResponse } from "@/types/today";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function getToday(): Promise<TodayResponse> {
  const response = await fetch(`${API_URL}/api/today`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load the MOVRvest morning brief.");
  }

  return response.json();
}
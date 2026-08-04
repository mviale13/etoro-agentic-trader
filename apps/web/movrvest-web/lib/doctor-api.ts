export type DoctorResponse = {
  health: number;
  diagnosis: string[];
  prescriptions: string[];
  projected_health: number;
  confidence: number;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function getDoctor(): Promise<DoctorResponse | null> {
  try {
    const response = await fetch(`${API_URL}/doctor`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch {
    return null;
  }
}
export type DataSource = "backend" | "fallback";

export type InvestorDNA = {
  confidence: number;
  message: string;
  status: "learning" | "developing" | "established" | "strong";
};

export type InvestorProfile = {
  completeness: number;
  completedFields: number;
  totalFields: number;
  status: "not_started" | "in_progress" | "complete";
};

export type InvestorUnderstanding = {
  profile: InvestorProfile;
  dna: InvestorDNA;
  source: DataSource;
  backendUrl: string;
  error?: string;
};

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

function clampPercentage(value: unknown): number {
  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return 0;
  }

  return Math.max(0, Math.min(100, Math.round(parsed)));
}

function getDNAStatus(
  confidence: number,
): InvestorDNA["status"] {
  if (confidence < 25) {
    return "learning";
  }

  if (confidence < 50) {
    return "developing";
  }

  if (confidence < 75) {
    return "established";
  }

  return "strong";
}

export async function getInvestorUnderstanding(): Promise<InvestorUnderstanding> {
  const endpoint = `${BACKEND_URL}/investor-dna/`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(
        `Investor DNA request failed with status ${response.status}`,
      );
    }

    const payload = (await response.json()) as {
      understanding?: unknown;
      message?: unknown;
    };

    const confidence = clampPercentage(payload.understanding);

    return {
      profile: {
        completeness: 0,
        completedFields: 0,
        totalFields: 10,
        status: "not_started",
      },
      dna: {
        confidence,
        message:
          typeof payload.message === "string"
            ? payload.message
            : "MOVRvest is learning your investment style.",
        status: getDNAStatus(confidence),
      },
      source: "backend",
      backendUrl: endpoint,
    };
  } catch (error) {
    return {
      profile: {
        completeness: 0,
        completedFields: 0,
        totalFields: 10,
        status: "not_started",
      },
      dna: {
        confidence: 0,
        message:
          "Investor DNA is temporarily unavailable while MOVRvest reconnects.",
        status: "learning",
      },
      source: "fallback",
      backendUrl: endpoint,
      error:
        error instanceof Error
          ? error.message
          : "Unknown backend connection error",
    };
  }
}

import type {
  ArtificialCioLearning,
  ArtificialCioResult,
  ArtificialCioViewModel,
  InvestmentPolicyItem,
} from "@/lib/view-models/artificial-cio";

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

type UnknownRecord = Record<string, unknown>;

const fallbackArtificialCio: ArtificialCioViewModel = {
  understanding: {
    value: "78%",
    detail: "Improving",
  },
  policyConfidence: {
    value: "High",
    detail: "Core preferences confirmed",
  },
  relationship: {
    value: "27 days",
    detail: "12 meaningful interactions",
  },
  openQuestionCount: {
    value: "3",
    detail: "To improve personalization",
  },
  investmentPolicy: [
    {
      label: "Primary objective",
      value: "Long-term growth",
    },
    {
      label: "Risk tolerance",
      value: "Moderate",
    },
    {
      label: "Investment horizon",
      value: "10+ years",
    },
    {
      label: "Portfolio approach",
      value: "Global equities",
    },
    {
      label: "Decision authority",
      value: "Investor approval required",
    },
  ],
  knowledgeItems: [
    "You prefer transparent recommendations with clear reasoning.",
    "You think in years rather than weeks.",
    "You value conviction more than frequent activity.",
    "You want to remain in control of every investment decision.",
  ],
  openQuestions: [
    "What is your preferred maximum position size?",
    "Should dividends be reinvested automatically?",
    "How much short-term volatility are you comfortable accepting?",
  ],
  recentLearning: [
    {
      title: "Cash strategy clarified",
      description:
        "Your CIO understands that available cash should be treated as optionality, not inactivity.",
      date: "Today",
    },
    {
      title: "Decision style updated",
      description:
        "You prefer fewer, higher-conviction recommendations supported by evidence.",
      date: "Recently",
    },
    {
      title: "Investment horizon confirmed",
      description:
        "Long-term compounding is more important than short-term market timing.",
      date: "Recently",
    },
  ],
};

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function recordAt(
  record: UnknownRecord,
  ...keys: string[]
): UnknownRecord | undefined {
  for (const key of keys) {
    const value = record[key];

    if (isRecord(value)) {
      return value;
    }
  }

  return undefined;
}

function valueAt(
  record: UnknownRecord | undefined,
  keys: readonly string[],
): unknown {
  if (!record) {
    return undefined;
  }

  for (const key of keys) {
    if (key in record) {
      return record[key];
    }
  }

  return undefined;
}

function stringAt(
  record: UnknownRecord | undefined,
  keys: readonly string[],
  fallback: string,
): string {
  const value = valueAt(record, keys);

  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }

  return fallback;
}

function numberAt(
  record: UnknownRecord | undefined,
  keys: readonly string[],
  fallback: number,
): number {
  const value = valueAt(record, keys);

  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const parsed = Number(value);

    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return fallback;
}

function normalizePercentage(value: number): string {
  const normalized = value <= 1 ? value * 100 : value;

  return `${Math.max(0, Math.min(100, Math.round(normalized)))}%`;
}

function normalizeConfidence(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.trim()) {
    const normalized = value.trim().toLowerCase();

    if (normalized === "high") return "High";
    if (normalized === "medium" || normalized === "moderate") return "Moderate";
    if (normalized === "low") return "Low";

    const numeric = Number(normalized);

    if (Number.isFinite(numeric)) {
      return confidenceLabel(numeric);
    }

    return value.trim();
  }

  if (typeof value === "number" && Number.isFinite(value)) {
    return confidenceLabel(value);
  }

  return fallback;
}

function confidenceLabel(value: number): string {
  const normalized = value <= 1 ? value * 100 : value;

  if (normalized >= 75) return "High";
  if (normalized >= 45) return "Moderate";
  return "Low";
}

function stringArrayAt(
  record: UnknownRecord | undefined,
  keys: readonly string[],
  fallback: string[],
): string[] {
  const value = valueAt(record, keys);

  if (!Array.isArray(value)) {
    return fallback;
  }

  const strings = value
    .map((item) => {
      if (typeof item === "string") {
        return item.trim();
      }

      if (isRecord(item)) {
        return stringAt(
          item,
          [
            "message",
            "description",
            "text",
            "question",
            "title",
            "statement",
            "value",
          ],
          "",
        );
      }

      return "";
    })
    .filter(Boolean);

  return strings.length > 0 ? strings : fallback;
}

function mapInvestmentPolicy(
  root: UnknownRecord,
): InvestmentPolicyItem[] {
  const policy =
    recordAt(
      root,
      "investment_policy",
      "investmentPolicy",
      "policy",
      "investor_profile",
      "investorProfile",
    ) ?? {};

  return [
    {
      label: "Primary objective",
      value: stringAt(
        policy,
        [
          "objective",
          "primary_objective",
          "primaryObjective",
          "investment_objective",
          "investmentObjective",
        ],
        fallbackArtificialCio.investmentPolicy[0].value,
      ),
    },
    {
      label: "Risk tolerance",
      value: stringAt(
        policy,
        [
          "risk_tolerance",
          "riskTolerance",
          "risk_profile",
          "riskProfile",
        ],
        fallbackArtificialCio.investmentPolicy[1].value,
      ),
    },
    {
      label: "Investment horizon",
      value: stringAt(
        policy,
        [
          "investment_horizon",
          "investmentHorizon",
          "time_horizon",
          "timeHorizon",
          "horizon",
        ],
        fallbackArtificialCio.investmentPolicy[2].value,
      ),
    },
    {
      label: "Portfolio approach",
      value: stringAt(
        policy,
        [
          "portfolio_approach",
          "portfolioApproach",
          "strategy",
          "approach",
          "asset_focus",
          "assetFocus",
        ],
        fallbackArtificialCio.investmentPolicy[3].value,
      ),
    },
    {
      label: "Decision authority",
      value: stringAt(
        policy,
        [
          "decision_authority",
          "decisionAuthority",
          "approval_policy",
          "approvalPolicy",
          "control",
        ],
        fallbackArtificialCio.investmentPolicy[4].value,
      ),
    },
  ];
}

function mapKnowledgeItems(root: UnknownRecord): string[] {
  const investorDna =
    recordAt(
      root,
      "investor_dna",
      "investorDna",
      "investor_profile",
      "investorProfile",
    ) ?? {};

  const directKnowledge = stringArrayAt(
    investorDna,
    [
      "knowledge",
      "beliefs",
      "observations",
      "preferences",
      "known_preferences",
      "knownPreferences",
    ],
    [],
  );

  if (directKnowledge.length > 0) {
    return directKnowledge.slice(0, 6);
  }

  const message = stringAt(
    investorDna,
    ["message", "summary", "description", "observation"],
    "",
  );

  if (message) {
    return [
      message,
      ...fallbackArtificialCio.knowledgeItems.slice(1),
    ];
  }

  const observation =
    recordAt(root, "observation", "investor_observation") ?? {};

  const observationMessage = stringAt(
    observation,
    ["message", "summary", "description", "text"],
    "",
  );

  if (observationMessage) {
    return [
      observationMessage,
      ...fallbackArtificialCio.knowledgeItems.slice(1),
    ];
  }

  return fallbackArtificialCio.knowledgeItems;
}

function mapOpenQuestions(root: UnknownRecord): string[] {
  const investorDna =
    recordAt(
      root,
      "investor_dna",
      "investorDna",
      "investor_profile",
      "investorProfile",
    ) ?? {};

  const questions = stringArrayAt(
    investorDna,
    [
      "open_questions",
      "openQuestions",
      "questions",
      "missing_information",
      "missingInformation",
    ],
    [],
  );

  if (questions.length > 0) {
    return questions.slice(0, 5);
  }

  return fallbackArtificialCio.openQuestions;
}

function mapRecentLearning(
  root: UnknownRecord,
): ArtificialCioLearning[] {
  const learning =
    valueAt(root, [
      "recent_learning",
      "recentLearning",
      "learning_history",
      "learningHistory",
      "timeline",
    ]) ?? [];

  if (!Array.isArray(learning)) {
    return fallbackArtificialCio.recentLearning;
  }

  const mapped = learning
    .map((item): ArtificialCioLearning | null => {
      if (typeof item === "string" && item.trim()) {
        return {
          title: "Understanding updated",
          description: item.trim(),
          date: "Recently",
        };
      }

      if (!isRecord(item)) {
        return null;
      }

      const description = stringAt(
        item,
        ["description", "message", "text", "summary"],
        "",
      );

      if (!description) {
        return null;
      }

      return {
        title: stringAt(
          item,
          ["title", "name", "event"],
          "Understanding updated",
        ),
        description,
        date: stringAt(
          item,
          ["date", "created_at", "createdAt", "timestamp"],
          "Recently",
        ),
      };
    })
    .filter(
      (item): item is ArtificialCioLearning =>
        item !== null,
    );

  return mapped.length > 0
    ? mapped.slice(0, 5)
    : fallbackArtificialCio.recentLearning;
}

function mapArtificialCio(
  root: UnknownRecord,
): ArtificialCioViewModel {
  const investorDna =
    recordAt(
      root,
      "investor_dna",
      "investorDna",
      "investor_profile",
      "investorProfile",
    ) ?? {};

  const understanding = numberAt(
    investorDna,
    [
      "confidence",
      "understanding",
      "understanding_score",
      "understandingScore",
      "profile_confidence",
      "profileConfidence",
    ],
    0.78,
  );

  const policy =
    recordAt(
      root,
      "investment_policy",
      "investmentPolicy",
      "policy",
    ) ?? {};

  const policyConfidence = valueAt(policy, [
    "confidence",
    "confidence_level",
    "confidenceLevel",
    "status",
  ]);

  const questions = mapOpenQuestions(root);

  const relationship =
    recordAt(
      root,
      "relationship",
      "investor_relationship",
      "investorRelationship",
    ) ?? {};

  const relationshipDays = numberAt(
    relationship,
    ["days", "age_days", "ageDays", "relationship_days"],
    27,
  );

  const interactions = numberAt(
    relationship,
    [
      "interactions",
      "interaction_count",
      "interactionCount",
      "meaningful_interactions",
      "meaningfulInteractions",
    ],
    12,
  );

  return {
    understanding: {
      value: normalizePercentage(understanding),
      detail: stringAt(
        investorDna,
        ["status", "confidence_label", "confidenceLabel"],
        "Improving",
      ),
    },
    policyConfidence: {
      value: normalizeConfidence(policyConfidence, "High"),
      detail: stringAt(
        policy,
        ["confidence_message", "confidenceMessage", "summary"],
        "Core preferences confirmed",
      ),
    },
    relationship: {
      value: `${relationshipDays} ${
        relationshipDays === 1 ? "day" : "days"
      }`,
      detail: `${interactions} meaningful ${
        interactions === 1 ? "interaction" : "interactions"
      }`,
    },
    openQuestionCount: {
      value: String(questions.length),
      detail: "To improve personalization",
    },
    investmentPolicy: mapInvestmentPolicy(root),
    knowledgeItems: mapKnowledgeItems(root),
    openQuestions: questions,
    recentLearning: mapRecentLearning(root),
  };
}

export async function getArtificialCio(): Promise<ArtificialCioResult> {
  const endpoint = `${BACKEND_URL}/brain/`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      const responseBody = await response.text();

      throw new Error(
        `Backend returned ${response.status}: ${responseBody.slice(0, 300)}`,
      );
    }

    const payload: unknown = await response.json();

    if (!isRecord(payload)) {
      throw new Error("The /brain response is not a JSON object.");
    }

    return {
      cio: mapArtificialCio(payload),
      source: "backend",
      backendUrl: endpoint,
    };
  } catch (error) {
    return {
      cio: fallbackArtificialCio,
      source: "fallback",
      backendUrl: endpoint,
      error:
        error instanceof Error
          ? error.message
          : "Unknown backend connection error",
    };
  }
}

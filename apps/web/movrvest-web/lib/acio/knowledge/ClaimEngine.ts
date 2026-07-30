import type {
  Claim,
  ClaimCategory,
  ClaimStatus,
  Evidence,
} from "./types";

export type CreateClaimInput = {
  readonly category: ClaimCategory;
  readonly title: string;
  readonly description: string;
  readonly confidence: number;
  readonly evidence?: readonly Evidence[];
  readonly assumptions?: readonly string[];
  readonly missingInformation?: readonly string[];
  readonly questions?: readonly string[];
  readonly generatedBy: string;
  readonly createdAt?: string;
};

export type UpdateClaimInput = {
  readonly title?: string;
  readonly description?: string;
  readonly confidence?: number;
  readonly evidence?: readonly Evidence[];
  readonly assumptions?: readonly string[];
  readonly missingInformation?: readonly string[];
  readonly questions?: readonly string[];
};

export type ClaimEngineDependencies = {
  readonly createId?: () => string;
  readonly now?: () => string;
};

const normalizeText = (
  value: string,
  fieldName: string,
): string => {
  const normalized = value.trim();

  if (normalized.length === 0) {
    throw new Error(`${fieldName} cannot be empty.`);
  }

  return normalized;
};

const normalizeStrings = (
  values: readonly string[] | undefined,
): string[] =>
  Array.from(
    new Set(
      (values ?? [])
        .map((value) => value.trim())
        .filter((value) => value.length > 0),
    ),
  );

const normalizeEvidence = (
  evidence: readonly Evidence[] | undefined,
): Evidence[] =>
  Array.from(
    new Map(
      (evidence ?? []).map((item) => [item.id, item]),
    ).values(),
  );

const validateConfidence = (
  confidence: number,
): number => {
  if (!Number.isFinite(confidence)) {
    throw new Error(
      "Claim confidence must be a finite number.",
    );
  }

  if (confidence < 0 || confidence > 1) {
    throw new Error(
      "Claim confidence must be between 0 and 1.",
    );
  }

  return confidence;
};

const requiresEvidence = (
  category: ClaimCategory,
): boolean =>
  category === "fact" ||
  category === "observation" ||
  category === "risk" ||
  category === "opportunity" ||
  category === "recommendation";

const validateEvidence = (
  category: ClaimCategory,
  evidence: readonly Evidence[],
): void => {
  if (requiresEvidence(category) && evidence.length === 0) {
    throw new Error(
      `Claim category "${category}" requires at least one evidence item.`,
    );
  }
};

const defaultCreateId = (): string => {
  if (
    typeof globalThis.crypto !== "undefined" &&
    typeof globalThis.crypto.randomUUID === "function"
  ) {
    return globalThis.crypto.randomUUID();
  }

  return [
    "claim",
    Date.now().toString(36),
    Math.random().toString(36).slice(2),
  ].join("-");
};

const defaultNow = (): string =>
  new Date().toISOString();

const freezeClaim = (claim: Claim): Claim =>
  Object.freeze({
    ...claim,
    evidence: Object.freeze([
      ...claim.evidence,
    ]) as unknown as Evidence[],
    assumptions: Object.freeze([
      ...claim.assumptions,
    ]) as unknown as string[],
    missingInformation: Object.freeze([
      ...claim.missingInformation,
    ]) as unknown as string[],
    questions: Object.freeze([
      ...claim.questions,
    ]) as unknown as string[],
  });

export class ClaimEngine {
  private readonly createId: () => string;

  private readonly now: () => string;

  constructor(
    dependencies: ClaimEngineDependencies = {},
  ) {
    this.createId =
      dependencies.createId ?? defaultCreateId;

    this.now = dependencies.now ?? defaultNow;
  }

  create(input: CreateClaimInput): Claim {
    const evidence = normalizeEvidence(
      input.evidence,
    );

    validateEvidence(input.category, evidence);

    const timestamp =
      input.createdAt ?? this.now();

    return freezeClaim({
      id: this.createId(),
      category: input.category,
      status: "generated",
      title: normalizeText(
        input.title,
        "Claim title",
      ),
      description: normalizeText(
        input.description,
        "Claim description",
      ),
      confidence: validateConfidence(
        input.confidence,
      ),
      evidence,
      assumptions: normalizeStrings(
        input.assumptions,
      ),
      missingInformation: normalizeStrings(
        input.missingInformation,
      ),
      questions: normalizeStrings(
        input.questions,
      ),
      generatedBy: normalizeText(
        input.generatedBy,
        "Claim generatedBy",
      ),
      createdAt: timestamp,
      updatedAt: timestamp,
    });
  }

  fact(
    input: Omit<CreateClaimInput, "category">,
  ): Claim {
    return this.create({
      ...input,
      category: "fact",
    });
  }

  observation(
    input: Omit<CreateClaimInput, "category">,
  ): Claim {
    return this.create({
      ...input,
      category: "observation",
    });
  }

  hypothesis(
    input: Omit<CreateClaimInput, "category">,
  ): Claim {
    return this.create({
      ...input,
      category: "hypothesis",
    });
  }

  risk(
    input: Omit<CreateClaimInput, "category">,
  ): Claim {
    return this.create({
      ...input,
      category: "risk",
    });
  }

  opportunity(
    input: Omit<CreateClaimInput, "category">,
  ): Claim {
    return this.create({
      ...input,
      category: "opportunity",
    });
  }

  recommendation(
    input: Omit<CreateClaimInput, "category">,
  ): Claim {
    return this.create({
      ...input,
      category: "recommendation",
    });
  }

  update(
    claim: Claim,
    input: UpdateClaimInput,
  ): Claim {
    this.ensureMutable(claim);

    const evidence =
      input.evidence === undefined
        ? claim.evidence
        : normalizeEvidence(input.evidence);

    validateEvidence(claim.category, evidence);

    return freezeClaim({
      ...claim,
      title:
        input.title === undefined
          ? claim.title
          : normalizeText(
              input.title,
              "Claim title",
            ),
      description:
        input.description === undefined
          ? claim.description
          : normalizeText(
              input.description,
              "Claim description",
            ),
      confidence:
        input.confidence === undefined
          ? claim.confidence
          : validateConfidence(
              input.confidence,
            ),
      evidence,
      assumptions:
        input.assumptions === undefined
          ? claim.assumptions
          : normalizeStrings(
              input.assumptions,
            ),
      missingInformation:
        input.missingInformation === undefined
          ? claim.missingInformation
          : normalizeStrings(
              input.missingInformation,
            ),
      questions:
        input.questions === undefined
          ? claim.questions
          : normalizeStrings(
              input.questions,
            ),
      updatedAt: this.now(),
    });
  }

  confirm(claim: Claim): Claim {
    this.ensureMutable(claim);

    return this.changeStatus(
      claim,
      "confirmed",
    );
  }

  reject(claim: Claim): Claim {
    if (claim.status === "superseded") {
      throw new Error(
        "Superseded claims cannot be rejected.",
      );
    }

    return this.changeStatus(
      claim,
      "rejected",
    );
  }

  supersede(claim: Claim): Claim {
    if (claim.status === "rejected") {
      throw new Error(
        "Rejected claims cannot be superseded.",
      );
    }

    return this.changeStatus(
      claim,
      "superseded",
    );
  }

  private ensureMutable(claim: Claim): void {
    if (claim.status === "rejected") {
      throw new Error(
        "Rejected claims cannot be modified.",
      );
    }

    if (claim.status === "superseded") {
      throw new Error(
        "Superseded claims cannot be modified.",
      );
    }
  }

  private changeStatus(
    claim: Claim,
    status: ClaimStatus,
  ): Claim {
    return freezeClaim({
      ...claim,
      status,
      updatedAt: this.now(),
    });
  }
}

export const claimEngine =
  new ClaimEngine();

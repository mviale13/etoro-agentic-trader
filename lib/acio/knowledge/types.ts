/**
 * MOVRvest Artificial Chief Investment Officer
 *
 * Knowledge Domain Model
 *
 * This file defines the core immutable domain objects used by the
 * Knowledge Engine.
 *
 * Architecture:
 *
 * Raw Data
 *     ↓
 * Evidence
 *     ↓
 * Claim
 *     ↓
 * Belief
 *     ↓
 * Knowledge
 *     ↓
 * Decision
 *     ↓
 * Outcome
 *     ↓
 * Learning
 */

export type UUID = string;
export type ISODateTime = string;

export type Confidence = number;

//
// -----------------------------------------------------------------------------
// ENUMS
// -----------------------------------------------------------------------------

export type EvidenceSource =
  | "portfolio"
  | "market"
  | "company"
  | "macro"
  | "news"
  | "investor"
  | "memory"
  | "system";

export type ClaimCategory =
  | "fact"
  | "observation"
  | "hypothesis"
  | "risk"
  | "opportunity"
  | "recommendation";

export type ClaimStatus =
  | "generated"
  | "confirmed"
  | "rejected"
  | "superseded";

export type BeliefState =
  | "candidate"
  | "accepted"
  | "confirmed"
  | "rejected";

export type KnowledgeStatus =
  | "active"
  | "challenged"
  | "deprecated"
  | "archived";

export type DecisionStatus =
  | "proposed"
  | "accepted"
  | "rejected"
  | "executed"
  | "expired";

//
// -----------------------------------------------------------------------------
// EVIDENCE
// -----------------------------------------------------------------------------

export interface Evidence {

  readonly id: UUID;

  readonly type: string;

  readonly subjectId: string;

  readonly statement: string;

  readonly value?: unknown;

  readonly source: EvidenceSource;

  readonly sourceReference?: string;

  readonly observedAt: ISODateTime;

  readonly recordedAt: ISODateTime;

  /**
   * 0 → 1
   */
  readonly reliability: number;

  /**
   * 0 → 1
   */
  readonly freshness: number;

  readonly metadata: Readonly<Record<string, unknown>>;
}

//
// -----------------------------------------------------------------------------
// CLAIM
// -----------------------------------------------------------------------------

export interface Claim {

  readonly id: UUID;

  readonly category: ClaimCategory;

  readonly subjectId: string;

  readonly statement: string;

  /**
   * Human-readable explanation.
   */
  readonly rationale?: string;

  /**
   * 0 → 1
   */
  readonly confidence: Confidence;

  readonly evidenceIds: readonly UUID[];

  readonly opposingEvidenceIds: readonly UUID[];

  readonly assumptions: readonly string[];

  readonly missingInformation: readonly string[];

  readonly questions: readonly string[];

  readonly createdBy: string;

  readonly createdAt: ISODateTime;

  readonly status: ClaimStatus;

  readonly supersededBy?: UUID;
}

//
// -----------------------------------------------------------------------------
// BELIEF
// -----------------------------------------------------------------------------

export interface Belief {

  readonly id: UUID;

  readonly claimId: UUID;

  readonly confidence: Confidence;

  readonly state: BeliefState;

  readonly validationCount: number;

  readonly contradictionCount: number;

  readonly firstAcceptedAt?: ISODateTime;

  readonly lastValidatedAt?: ISODateTime;

  readonly lastChallengedAt?: ISODateTime;

  readonly context: Readonly<Record<string, unknown>>;
}

//
// -----------------------------------------------------------------------------
// KNOWLEDGE
// -----------------------------------------------------------------------------

export interface KnowledgeItem {

  readonly id: UUID;

  readonly subjectId: string;

  readonly statement: string;

  readonly beliefId: UUID;

  readonly confidence: Confidence;

  readonly validationBasis: readonly string[];

  readonly provenance: readonly string[];

  readonly effectiveFrom: ISODateTime;

  readonly lastReviewedAt: ISODateTime;

  readonly reviewAfter?: ISODateTime;

  readonly status: KnowledgeStatus;
}

//
// -----------------------------------------------------------------------------
// DECISION
// -----------------------------------------------------------------------------

export interface Decision {

  readonly id: UUID;

  readonly subjectId: string;

  readonly action: string;

  readonly rationale: string;

  readonly claimIds: readonly UUID[];

  readonly knowledgeIds: readonly UUID[];

  readonly confidence: Confidence;

  readonly alternatives: readonly string[];

  readonly constraints: readonly string[];

  readonly investorRelevance: string;

  readonly status: DecisionStatus;

  readonly createdAt: ISODateTime;
}

//
// -----------------------------------------------------------------------------
// OUTCOME
// -----------------------------------------------------------------------------

export interface Outcome {

  readonly id: UUID;

  readonly decisionId: UUID;

  readonly observedAt: ISODateTime;

  readonly summary: string;

  readonly successful: boolean;

  readonly observations: readonly string[];

  readonly lessons: readonly string[];

  readonly metadata: Readonly<Record<string, unknown>>;
}

//
// -----------------------------------------------------------------------------
// KNOWLEDGE BASE
// -----------------------------------------------------------------------------

export interface KnowledgeBase {

  readonly evidence: readonly Evidence[];

  readonly claims: readonly Claim[];

  readonly beliefs: readonly Belief[];

  readonly knowledge: readonly KnowledgeItem[];

  readonly decisions: readonly Decision[];

  readonly outcomes: readonly Outcome[];
}

//
// -----------------------------------------------------------------------------
// REASONER CONTRACT
// -----------------------------------------------------------------------------

export interface ReasoningContext {

  readonly evidence: readonly Evidence[];

  readonly knowledge: readonly KnowledgeItem[];
}

export interface Reasoner {

  readonly name: string;

  readonly version: string;

  reason(
    context: ReasoningContext,
  ): readonly Claim[];
}

import type { EvidenceKind } from "@/lib/acio/ontology";

export type EvidenceSource =
  | "portfolio"
  | "transaction"
  | "market"
  | "company"
  | "macro"
  | "investor"
  | "news"
  | "memory";

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

export interface Evidence {
  id: string;

  source: EvidenceSource;

  /**
   * Stable machine-readable identifier from the ACIO ontology.
   */
  kind: EvidenceKind;

  /**
   * Human-readable label.
   */
  title: string;

  /**
   * Human-readable explanation of the observed fact.
   */
  description: string;

  /**
   * Reliability of the evidence.
   * Range: 0..1
   */
  strength: number;

  /**
   * Structured values used by reasoners.
   *
   * Human-readable text must never be parsed to recover data.
   */
  metadata?: Record<string, unknown>;
}

export interface Claim {
  id: string;

  category: ClaimCategory;

  status: ClaimStatus;

  title: string;

  description: string;

  /**
   * Confidence in the interpretation.
   * Range: 0..1
   */
  confidence: number;

  evidence: Evidence[];

  assumptions: string[];

  missingInformation: string[];

  questions: string[];

  generatedBy: string;

  createdAt: string;

  updatedAt: string;
}

export interface KnowledgeBase {
  claims: Claim[];
}

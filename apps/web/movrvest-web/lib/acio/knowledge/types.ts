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

  title: string;

  description: string;

  strength: number;

  metadata?: Record<string, unknown>;
}

export interface Claim {
  id: string;

  category: ClaimCategory;

  status: ClaimStatus;

  title: string;

  description: string;

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

import type { Claim } from "@/lib/acio/knowledge/types";

import type {
  InvestorAnalysis,
  InvestorFact,
  InvestorHypothesis,
  InvestorObservation,
} from "./types";

function getFactValue(claim: Claim): string {
  const value = claim.evidence[0]?.metadata?.displayValue;

  return typeof value === "string" ? value : "—";
}

function getEvidenceDescriptions(claim: Claim): string[] {
  return claim.evidence.map((evidence) => evidence.description);
}

export function createInvestorAnalysisFromClaims(
  claims: Claim[],
): InvestorAnalysis {
  const facts: InvestorFact[] = claims
    .filter((claim) => claim.category === "fact")
    .map((claim) => ({
      id: claim.id,
      title: claim.title,
      value: getFactValue(claim),
    }));

  const observations: InvestorObservation[] = claims
    .filter((claim) => claim.category === "observation")
    .map((claim) => ({
      id: claim.id,
      title: claim.title,
      description: claim.description,
    }));

  const hypotheses: InvestorHypothesis[] = claims
    .filter((claim) => claim.category === "hypothesis")
    .map((claim) => ({
      id: claim.id,
      title: claim.title,
      confidence: claim.confidence,
      evidence: getEvidenceDescriptions(claim),
    }));

  return {
    facts,
    observations,
    hypotheses,
  };
}

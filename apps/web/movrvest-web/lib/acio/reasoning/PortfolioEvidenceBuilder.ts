import type { Evidence } from "@/lib/acio/knowledge/types";
import { PortfolioEvidenceKinds } from "@/lib/acio/ontology";
import type { PortfolioSnapshot } from "@/lib/acio/reasoning/PortfolioReasoner";

export class PortfolioEvidenceBuilder {
  build(snapshot: PortfolioSnapshot): Evidence[] {
    return [
      {
        id: crypto.randomUUID(),
        source: "portfolio",
        kind: PortfolioEvidenceKinds.PortfolioValue,
        title: "Portfolio Value",
        description: `Portfolio value is $${snapshot.portfolioValue.toLocaleString(
          "en-US",
        )}.`,
        strength: 1,
        metadata: {
          value: snapshot.portfolioValue,
        },
      },
      {
        id: crypto.randomUUID(),
        source: "portfolio",
        kind: PortfolioEvidenceKinds.CashBalance,
        title: "Cash Balance",
        description: `Available cash is $${snapshot.availableCash.toLocaleString(
          "en-US",
        )}.`,
        strength: 1,
        metadata: {
          value: snapshot.availableCash,
        },
      },
      {
        id: crypto.randomUUID(),
        source: "portfolio",
        kind: PortfolioEvidenceKinds.InvestedValue,
        title: "Invested Value",
        description: `Invested value is $${snapshot.investedValue.toLocaleString(
          "en-US",
        )}.`,
        strength: 1,
        metadata: {
          value: snapshot.investedValue,
        },
      },
      {
        id: crypto.randomUUID(),
        source: "portfolio",
        kind: PortfolioEvidenceKinds.PositionCount,
        title: "Open Positions",
        description: `${snapshot.positionsCount} active positions detected.`,
        strength: 1,
        metadata: {
          value: snapshot.positionsCount,
        },
      },
    ];
  }
}

export const portfolioEvidenceBuilder =
  new PortfolioEvidenceBuilder();

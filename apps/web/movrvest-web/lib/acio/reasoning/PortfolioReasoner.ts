import { PortfolioEvidenceKinds } from "@/lib/acio/ontology";
import type {
  Claim,
  Evidence,
} from "@/lib/acio/knowledge/types";

export type PortfolioSnapshot = {
  portfolioValue: number;
  availableCash: number;
  investedValue: number;
  positionsCount: number;
  pendingOrdersCount: number;
  historicalTransactionsCount: number;
};

function createEvidence(
  id: string,
  title: string,
  description: string,
  metadata?: Record<string, unknown>,
): Evidence {
  return {
    id,
    source: "portfolio",
    kind: PortfolioEvidenceKinds.CashBalance,
    title,
    description,
    strength: 100,
    metadata,
  };
}

function createClaim({
  id,
  category,
  title,
  description,
  confidence,
  evidence,
  assumptions = [],
  missingInformation = [],
  questions = [],
  generatedAt,
}: {
  id: string;
  category: Claim["category"];
  title: string;
  description: string;
  confidence: number;
  evidence: Evidence[];
  assumptions?: string[];
  missingInformation?: string[];
  questions?: string[];
  generatedAt: string;
}): Claim {
  return {
    id,
    category,
    status: "generated",
    title,
    description,
    confidence,
    evidence,
    assumptions,
    missingInformation,
    questions,
    generatedBy: "PortfolioReasoner",
    createdAt: generatedAt,
    updatedAt: generatedAt,
  };
}

export class PortfolioReasoner {
  reason(snapshot: PortfolioSnapshot): Claim[] {
    const generatedAt = new Date().toISOString();

    const cashAllocation =
      snapshot.portfolioValue > 0
        ? snapshot.availableCash / snapshot.portfolioValue
        : 0;

    const investedAllocation =
      snapshot.portfolioValue > 0
        ? snapshot.investedValue / snapshot.portfolioValue
        : 0;

    const claims: Claim[] = [
      createClaim({
        id: "portfolio-value",
        category: "fact",
        title: "Portfolio value",
        description: "The current total portfolio value.",
        confidence: 100,
        evidence: [
          createEvidence(
            "portfolio-value-evidence",
            "Portfolio value",
            `Portfolio value is $${snapshot.portfolioValue.toLocaleString(
              "en-US",
            )}.`,
            {
              displayValue: `$${snapshot.portfolioValue.toLocaleString(
                "en-US",
              )}`,
              numericValue: snapshot.portfolioValue,
            },
          ),
        ],
        generatedAt,
      }),

      createClaim({
        id: "available-cash",
        category: "fact",
        title: "Available cash",
        description: "The amount currently available for deployment.",
        confidence: 100,
        evidence: [
          createEvidence(
            "available-cash-evidence",
            "Available cash",
            `Available cash is $${snapshot.availableCash.toLocaleString(
              "en-US",
            )}.`,
            {
              displayValue: `$${snapshot.availableCash.toLocaleString(
                "en-US",
              )}`,
              numericValue: snapshot.availableCash,
            },
          ),
        ],
        generatedAt,
      }),

      createClaim({
        id: "current-positions",
        category: "fact",
        title: "Current positions",
        description: "The number of active portfolio positions.",
        confidence: 100,
        evidence: [
          createEvidence(
            "current-positions-evidence",
            "Current positions",
            `${snapshot.positionsCount} active positions were detected.`,
            {
              displayValue: snapshot.positionsCount.toString(),
              numericValue: snapshot.positionsCount,
            },
          ),
        ],
        generatedAt,
      }),

      createClaim({
        id: "historical-transactions",
        category: "fact",
        title: "Historical transactions",
        description:
          "The number of historical transactions currently available for behavioural analysis.",
        confidence: 100,
        evidence: [
          createEvidence(
            "historical-transactions-evidence",
            "Historical transactions",
            `${snapshot.historicalTransactionsCount} historical transactions are available.`,
            {
              displayValue:
                snapshot.historicalTransactionsCount.toString(),
              numericValue: snapshot.historicalTransactionsCount,
            },
          ),
        ],
        generatedAt,
      }),
    ];

    if (cashAllocation >= 0.8) {
      claims.push(
        createClaim({
          id: "high-liquidity",
          category: "observation",
          title: "Portfolio is highly liquid",
          description: `${Math.round(
            cashAllocation * 100,
          )}% of the portfolio is currently held in cash.`,
          confidence: 100,
          evidence: [
            createEvidence(
              "cash-allocation-evidence",
              "Cash allocation",
              `${Math.round(
                cashAllocation * 100,
              )}% of portfolio value is available cash.`,
              {
                cashAllocation,
                availableCash: snapshot.availableCash,
                portfolioValue: snapshot.portfolioValue,
              },
            ),
          ],
          generatedAt,
        }),
      );
    }

    if (snapshot.positionsCount === 0) {
      claims.push(
        createClaim({
          id: "no-active-investments",
          category: "observation",
          title: "No active investments",
          description:
            "The portfolio currently contains no open investment positions.",
          confidence: 100,
          evidence: [
            createEvidence(
              "zero-positions-evidence",
              "Position count",
              "The current position count is zero.",
              {
                positionsCount: snapshot.positionsCount,
              },
            ),
          ],
          generatedAt,
        }),
      );
    }

    if (
      cashAllocation >= 0.8 &&
      snapshot.positionsCount === 0
    ) {
      claims.push(
        createClaim({
          id: "deployment-flexibility",
          category: "observation",
          title: "High deployment flexibility",
          description:
            "The current portfolio structure allows substantial freedom when constructing the desired future portfolio.",
          confidence: 96,
          evidence: [
            createEvidence(
              "deployment-cash-evidence",
              "High cash allocation",
              `${Math.round(
                cashAllocation * 100,
              )}% of the portfolio is held in cash.`,
              {
                cashAllocation,
              },
            ),
            createEvidence(
              "deployment-positions-evidence",
              "No active positions",
              "There are no existing positions constraining portfolio construction.",
              {
                positionsCount: snapshot.positionsCount,
              },
            ),
          ],
          generatedAt,
        }),
      );
    }

    if (
      snapshot.historicalTransactionsCount > 0 &&
      snapshot.positionsCount === 0
    ) {
      claims.push(
        createClaim({
          id: "transition-period",
          category: "hypothesis",
          title: "You may be in a portfolio transition period",
          description:
            "Historical investment activity exists, but the current portfolio has no active positions.",
          confidence: 78,
          evidence: [
            createEvidence(
              "transition-history-evidence",
              "Historical activity",
              `${snapshot.historicalTransactionsCount} historical transactions are available.`,
              {
                historicalTransactionsCount:
                  snapshot.historicalTransactionsCount,
              },
            ),
            createEvidence(
              "transition-current-state-evidence",
              "Current portfolio state",
              "The portfolio currently contains no active positions.",
              {
                positionsCount: snapshot.positionsCount,
              },
            ),
          ],
          assumptions: [
            "The absence of active positions is intentional rather than caused by incomplete account synchronization.",
          ],
          missingInformation: [
            "Why the previous portfolio positions were closed.",
            "Whether the investor is preparing to adopt a new strategy.",
          ],
          questions: [
            "Are you intentionally rebuilding your portfolio from cash?",
          ],
          generatedAt,
        }),
      );
    }

    if (investedAllocation === 0) {
      claims.push(
        createClaim({
          id: "future-portfolio-different",
          category: "hypothesis",
          title:
            "Your future portfolio may differ significantly from your historical portfolio",
          description:
            "The current fully liquid position creates an opportunity to define a portfolio from present goals rather than reproduce previous allocations.",
          confidence: 85,
          evidence: [
            createEvidence(
              "future-portfolio-cash-evidence",
              "Fully liquid portfolio",
              "No portfolio value is currently invested.",
              {
                investedAllocation,
                investedValue: snapshot.investedValue,
              },
            ),
            createEvidence(
              "future-portfolio-history-evidence",
              "Historical evidence exists",
              `${snapshot.historicalTransactionsCount} historical transactions can inform—but should not determine—the future strategy.`,
              {
                historicalTransactionsCount:
                  snapshot.historicalTransactionsCount,
              },
            ),
          ],
          assumptions: [
            "The investor is open to reconsidering previous portfolio construction choices.",
          ],
          missingInformation: [
            "Current investment objectives.",
            "Desired risk level.",
            "Investment horizon.",
          ],
          questions: [
            "What should your next portfolio help you achieve?",
          ],
          generatedAt,
        }),
      );
    }

    return claims;
  }
}

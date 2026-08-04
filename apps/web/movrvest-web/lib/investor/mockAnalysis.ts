import {
  PortfolioReasoner,
  type PortfolioSnapshot,
} from "@/lib/acio/reasoning/PortfolioReasoner";

import { createInvestorAnalysisFromClaims } from "./fromPortfolioClaims";

const demoPortfolioSnapshot: PortfolioSnapshot = {
  portfolioValue: 100_000,
  availableCash: 100_000,
  investedValue: 0,
  positionsCount: 0,
  pendingOrdersCount: 0,
  historicalTransactionsCount: 137,
};

const portfolioReasoner = new PortfolioReasoner();

const portfolioClaims = portfolioReasoner.reason(
  demoPortfolioSnapshot,
);

export const mockInvestorAnalysis =
  createInvestorAnalysisFromClaims(portfolioClaims);

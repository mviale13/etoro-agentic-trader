import type { ExecutiveWorkspaceViewModel } from "@/types/executive-workspace";

export const executiveWorkspaceMock: ExecutiveWorkspaceViewModel = {
  greeting: "Good morning, Marcos.",
  dateLabel: "Tuesday, July 28",
  briefing:
    "Two investment dossiers deserve your attention. Your portfolio remains healthy, while improving market breadth supports a more constructive outlook.",
  priorities: [
    {
      symbol: "MSFT",
      name: "Microsoft",
      executiveScore: 92,
      summary: "Enterprise AI demand and Azure momentum continue to strengthen.",
      rationale:
        "Committee alignment is strong, but valuation remains the principal risk.",
      href: "/dossiers/MSFT",
    },
    {
      symbol: "NVO",
      name: "Novo Nordisk",
      executiveScore: 87,
      summary: "The recent correction may have improved the long-term risk/reward.",
      rationale:
        "Fundamentals remain attractive while short-term uncertainty has increased.",
      href: "/dossiers/NVO",
    },
  ],
  portfolio: {
    grade: "A−",
    status: "Healthy",
    summary:
      "Diversification is improving and all major exposures remain within policy.",
    riskLevel: "Moderate",
    cashAllocation: 12,
  },
  market: {
    headline: "Market breadth is improving.",
    summary:
      "Participation has broadened beyond the largest technology companies, making the current advance more resilient.",
    signals: [
      "Volatility has eased",
      "Two sectors are outperforming",
      "Central-bank speakers are scheduled today",
    ],
  },
  importantEvent: {
    title: "NVIDIA earnings",
    timing: "Tomorrow · 22:00 CET",
    summary:
      "Results may affect semiconductor exposure and broader expectations for AI infrastructure spending.",
    href: "/events/nvda-earnings",
  },
};

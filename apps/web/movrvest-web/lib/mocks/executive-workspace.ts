import type { ExecutiveWorkspaceViewModel } from "@/lib/view-models/executive-workspace";

export const executiveWorkspaceMock: ExecutiveWorkspaceViewModel = {
  lastReviewedAt: "Wednesday, July 29 · 08:12",
  situation: "attention",
  headline: "Three things deserve your attention.",
  summary:
    "The Artificial CIO completed its latest review. Portfolio health remains stable, while three developments warrant closer attention. No immediate trade is required.",

  reviewed: {
    portfolioHoldings: 18,
    companies: 2483,
    marketEvents: 187,
    macroIndicators: 41,
  },

  changes: [
    {
      id: "nvidia-conviction",
      severity: "important",
      title: "NVIDIA conviction increased",
      detail: "Executive conviction moved from 68% to 82%.",
      context: "Earnings revisions and margin strength improved the investment case.",
      href: "/research/nvidia",
    },
    {
      id: "portfolio-risk",
      severity: "attention",
      title: "Technology concentration increased",
      detail: "Portfolio exposure moved 2.3 percentage points higher.",
      context: "The allocation remains within policy but is approaching its preferred range.",
      href: "/portfolio",
    },
    {
      id: "fed-expectations",
      severity: "information",
      title: "Rate expectations became more supportive",
      detail: "Markets are now pricing a more constructive rate path.",
      context: "Growth assets may benefit, although the signal remains sensitive to inflation data.",
      href: "/markets",
    },
    {
      id: "additional-changes",
      severity: "information",
      title: "Eight additional changes were reviewed",
      detail: "None currently require direct action.",
      context: "They remain available in the decision timeline.",
      href: "/journal",
    },
  ],

  priorities: [
    {
      id: "review-nvidia",
      urgency: "now",
      title: "Review the NVIDIA investment case",
      rationale:
        "Conviction increased materially and the underlying thesis has been updated.",
      estimatedMinutes: 4,
      href: "/research/nvidia",
    },
    {
      id: "review-allocation",
      urgency: "today",
      title: "Review technology allocation",
      rationale:
        "Concentration increased and is moving toward the upper end of your preferred range.",
      estimatedMinutes: 2,
      href: "/portfolio",
    },
    {
      id: "read-asml",
      urgency: "monitor",
      title: "Read the updated ASML dossier",
      rationale:
        "The company remains one of the strongest opportunities in the current research queue.",
      estimatedMinutes: 5,
      href: "/research/asml",
    },
  ],
};

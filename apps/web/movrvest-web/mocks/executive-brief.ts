import type { ExecutiveBriefViewModel } from "@/types/executive-brief";

export const microsoftExecutiveBrief: ExecutiveBriefViewModel = {
  symbol: "MSFT",
  companyName: "Microsoft Corporation",
  sector: "Technology",
  executiveScore: 92,
  attentionLabel: "Worth your attention this week",
  readingTime: "2 min read",
  generatedAt: "Generated today at 08:15",
  executiveSummary:
    "Microsoft continues strengthening its position as a leader in enterprise AI. Azure growth remains robust, enterprise adoption continues accelerating, and recent market volatility has not materially changed the long-term investment thesis.",
  whyNow: [
    "Azure growth exceeded expectations",
    "AI infrastructure spending accelerated",
    "Your allocation is below policy target",
    "Committee conviction increased",
  ],
  committees: [
    { name: "Portfolio", verdict: "Strong support" },
    { name: "Market", verdict: "Strong support" },
    { name: "Opportunity", verdict: "Support" },
    { name: "Risk", verdict: "Neutral" },
    { name: "Policy", verdict: "Strong support" },
  ],
  portfolioImpact: {
    currentAllocation: "4.2%",
    suggestedAllocation: "Approximately 5%",
    cashRequired: "0.8%",
    policyStatus: "Within limits",
  },
  evidence: [
    {
      label: "Azure revenue",
      value: "+31%",
      explanation: "Cloud growth remains a key driver of the investment thesis.",
    },
    {
      label: "Free cash flow",
      value: "Record high",
      explanation: "Strong cash generation supports resilience and reinvestment.",
    },
    {
      label: "Cloud backlog",
      value: "Growing",
      explanation: "Demand visibility continues improving.",
    },
    {
      label: "AI adoption",
      value: "Accelerating",
      explanation: "Enterprise adoption is broadening across products.",
    },
  ],
  risks: [
    "Valuation remains above historical averages",
    "Competition from AWS and Google remains significant",
    "AI monetization execution may take longer than expected",
    "A macroeconomic slowdown could affect enterprise spending",
  ],
  executiveAssessment: [
    "This investment remains aligned with your long-term investment policy.",
    "Current evidence supports further consideration.",
    "No immediate action is required.",
    "The final investment decision remains yours.",
  ],
};

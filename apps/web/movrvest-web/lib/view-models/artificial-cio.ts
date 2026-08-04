export interface ArtificialCioMetric {
  value: string;
  detail: string;
}

export interface InvestmentPolicyItem {
  label: string;
  value: string;
}

export interface ArtificialCioLearning {
  title: string;
  description: string;
  date: string;
}

export interface ArtificialCioViewModel {
  understanding: ArtificialCioMetric;
  policyConfidence: ArtificialCioMetric;
  relationship: ArtificialCioMetric;
  openQuestionCount: ArtificialCioMetric;

  investmentPolicy: InvestmentPolicyItem[];
  knowledgeItems: string[];
  openQuestions: string[];
  recentLearning: ArtificialCioLearning[];
}

export interface ArtificialCioResult {
  cio: ArtificialCioViewModel;
  source: "backend" | "fallback";
  backendUrl: string;
  error?: string;
}

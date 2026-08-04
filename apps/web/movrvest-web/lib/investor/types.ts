export type InvestorFact = {
  id: string;
  title: string;
  value: string;
};

export type InvestorObservation = {
  id: string;
  title: string;
  description: string;
};

export type InvestorHypothesis = {
  id: string;
  title: string;
  confidence: number;
  evidence: string[];
};

export type InvestorAnalysis = {
  facts: InvestorFact[];
  observations: InvestorObservation[];
  hypotheses: InvestorHypothesis[];
};

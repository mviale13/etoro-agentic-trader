export type TodayResponse = {
  greeting: string;
  health: {
    score: number;
  };
  summary: string;
  changes: string[];
  recommendation: {
    symbol: string;
    action: string;
    confidence: number;
  };
  next_action: string;
};
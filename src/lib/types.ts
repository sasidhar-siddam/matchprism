export type Grade = "A+" | "A" | "B" | "C" | "D";

export type TeamCode =
  | "RCB"
  | "SRH"
  | "CSK"
  | "MI"
  | "KKR"
  | "DC"
  | "RR"
  | "PBKS"
  | "GT"
  | "LSG";

export interface AdvancedAnalysisRow {
  outcome: string;
  modelProb: number;
  impliedProb: number;
  edge: number;
  verdict: "VALUE" | "FAIR" | "AVOID";
}

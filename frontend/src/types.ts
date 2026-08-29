// Types for HalluGuard frontend

export type AIModel = {
  id: string; // e.g., 'gpt-4o'
  name: string; // display name
};

export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string; // ISO string
};

export type Evidence = {
  id: string;
  title: string;
  snippet: string;
  url: string;
};

export type Claim = {
  id: string;
  text: string;
  confidenceScore: number; // 0-1
  evidence: Evidence[];
};

export type AnalysisReport = {
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  riskScore: number; // 0-100 percentage
  totalClaims: number;
  supportedClaims: number;
  uncertainClaims: number;
  contradictedClaims: number;
  claims: Claim[];
};

export type Chat = {
  id: string;
  title: string; // usually first user message
  modelId: string;
  messages: Message[];
  analysis?: AnalysisReport;
};

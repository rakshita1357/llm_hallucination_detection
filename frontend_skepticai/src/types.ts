export type ModelId = 'gemini-2-5-pro' | 'gemini-2-5-flash' | 'nvidia-nim-gpt-oss-120b' | 'nvidia/nemotron-3-super-120b-a12b' | 'google/gemma-4-31b-it';

export interface AIModel {
  id: ModelId;
  name: string;
  provider: 'OpenAI' | 'Google' | 'Anthropic' | 'NVIDIA';
  description: string;
  contextWindow: string;
  tag: string;
  badgeColor: string;
  iconName: string;
}

export type VerificationStatus = 
  | 'verified' 
  | 'mostly_reliable' 
  | 'partially_reliable' 
  | 'potential_hallucination' 
  | 'analysis_unavailable';

export type FindingStatus = 
  | 'unsupported' 
  | 'contradicted' 
  | 'low_confidence' 
  | 'misattributed' 
  | 'verified';

export interface SourceReference {
  title: string;
  url: string;
  domain?: string;
  snippet?: string;
  retrievalScore?: number;
}

export interface AnalysisFinding {
  id: string;
  claim: string;
  status: FindingStatus;
  confidence: number; // 0.00 - 1.00
  reason: string;
  evidence: string;
  source?: SourceReference;
  retrievalStatus?: 'verified_match' | 'no_evidence_found' | 'conflicting_evidence' | 'outdated_knowledge';
}

export interface AnalysisReportData {
  confidence: number; // 0.00 - 1.00
  status: VerificationStatus;
  summary?: string;
  totalClaimsCount?: number;
  verifiedClaimsCount?: number;
  flaggedFindingsCount?: number;
  findings: AnalysisFinding[];
  analyzedAt?: string;
  modelUsed?: string;
  latencyMs?: number;
  pipelineStepsCompleted?: number;
}

export interface AttachedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  contentPreview?: string;
  uploadedAt: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  modelId?: ModelId;
  attachments?: AttachedFile[];
  analysis?: AnalysisReportData;
  analysisStatus?: 'idle' | 'analyzing' | 'completed' | 'failed' | 'unavailable';
  analysisStep?: number; // 0: response generated, 1: extracting claims, 2: checking evidence, 3: evaluating claims, 4: calculating confidence
  feedback?: 'like' | 'dislike' | null;
}

export interface ChatConversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  modelId: ModelId;
  messages: ChatMessage[];
  pinned?: boolean;
}

export interface UserSettings {
  theme: 'dark' | 'light' | 'system';
  defaultModel: ModelId;
  enterToSend: boolean;
  enableAnalysisReport: boolean;
  showConfidenceScores: boolean;
  showEvidenceSources: boolean;
  autoOpenFindings: boolean;
  highlightFlaggedText: boolean;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
  role: string;
  isLoggedIn: boolean;
}

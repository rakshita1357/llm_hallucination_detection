import { AIModel } from '../types.ts';

export const AVAILABLE_MODELS: AIModel[] = [
  {
    id: 'chatgpt-4o',
    name: 'ChatGPT-4o',
    provider: 'OpenAI',
    description: 'Flagship multimodal model with broad general knowledge and rapid reasoning.',
    contextWindow: '128k tokens',
    tag: 'OpenAI GPT-4o',
    badgeColor: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    iconName: 'chatgpt'
  },
  {
    id: 'gemini-2-5-pro',
    name: 'Gemini 2.5 Pro',
    provider: 'Google',
    description: 'Deep analytical capabilities, state-of-the-art coding and nuanced factual recall.',
    contextWindow: '1M tokens',
    tag: 'Google DeepMind',
    badgeColor: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    iconName: 'gemini'
  },
  {
    id: 'claude-3-5-sonnet',
    name: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    description: 'Industry-leading nuanced synthesis, precision writing, and logical comprehension.',
    contextWindow: '200k tokens',
    tag: 'Anthropic Claude',
    badgeColor: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
    iconName: 'claude'
  }
];

export const DEFAULT_MODEL_ID = 'gemini-2-5-pro';

export const PIPELINE_STEPS = [
  { id: 0, label: 'Response generated', detail: 'LLM completion streamed' },
  { id: 1, label: 'Extracting factual claims', detail: 'Decomposing response into atomic atomic claim triples' },
  { id: 2, label: 'Checking retrieved evidence', detail: 'Querying knowledge corpus and web indexes' },
  { id: 3, label: 'Evaluating claims vs evidence', detail: 'Cross-verifying entailment and contradiction' },
  { id: 4, label: 'Calculating confidence & calibration', detail: 'Synthesizing aggregate reliability metric' },
];

import { AIModel } from '../types.ts';

export const AVAILABLE_MODELS: AIModel[] = [
  {
    id: 'nvidia-nim-gpt-oss-120b',
    name: 'GPT-OSS 120B (NVIDIA NIM)',
    provider: 'NVIDIA',
    description: 'Open-weight 120B model served via NVIDIA NIM, OpenAI-compatible endpoint.',
    contextWindow: '128k tokens',
    tag: 'NVIDIA NIM',
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
    id: 'nvidia/nemotron-3-super-120b-a12b',
    name: 'Nemotron 3 Super 120B (NVIDIA NIM)',
    provider: 'NVIDIA',
    description: 'Lightweight 120B MoE model with 12B active params, optimized for verification.',
    contextWindow: '128k tokens',
    tag: 'NVIDIA NIM',
    badgeColor: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    iconName: 'cpu'
  },
  {
    id: 'google/gemma-4-31b-it',
    name: 'Gemma 4 31B IT (NVIDIA NIM)',
    provider: 'Google',
    description: 'Lightweight 31B instruction-tuned model, optimized for verification.',
    contextWindow: '128k tokens',
    tag: 'NVIDIA NIM',
    badgeColor: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    iconName: 'gemini'
  },

];

export const DEFAULT_MODEL_ID = 'gemini-2-5-pro';

export const PIPELINE_STEPS = [
  { id: 0, label: 'Response generated', detail: 'LLM completion streamed' },
  { id: 1, label: 'Extracting factual claims', detail: 'Decomposing response into atomic atomic claim triples' },
  { id: 2, label: 'Checking retrieved evidence', detail: 'Querying knowledge corpus and web indexes' },
  { id: 3, label: 'Evaluating claims vs evidence', detail: 'Cross-verifying entailment and contradiction' },
  { id: 4, label: 'Calculating confidence & calibration', detail: 'Synthesizing aggregate reliability metric' },
];

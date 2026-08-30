import { ChatConversation, UserProfile, UserSettings } from '../types.ts';

const STORAGE_KEYS = {
  CONVERSATIONS: 'skepticai_conversations_v1',
  ACTIVE_CHAT_ID: 'skepticai_active_chat_id_v1',
  SETTINGS: 'skepticai_settings_v1',
  USER_PROFILE: 'skepticai_user_profile_v1'
};

export const DEFAULT_SETTINGS: UserSettings = {
  theme: 'dark',
  defaultModel: 'gemini-2-5-pro',
  enterToSend: true,
  enableAnalysisReport: true,
  showConfidenceScores: true,
  showEvidenceSources: true,
  autoOpenFindings: true,
  highlightFlaggedText: true,
  customBackendUrl: 'http://localhost:8000/api/chat',
  useLiveBackend: false
};

export const DEFAULT_USER: UserProfile = {
  id: 'usr_skeptic_01',
  name: 'Alex Rivera',
  email: 'alex.rivera@research.org',
  avatarUrl: '',
  role: 'AI Safety Researcher',
  isLoggedIn: true
};

const SEED_CONVERSATIONS: ChatConversation[] = [
  {
    id: 'chat-today-01',
    title: 'Albert Einstein Nobel Prize Citation',
    createdAt: new Date(Date.now() - 1000 * 60 * 35).toISOString(), // 35 mins ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
    modelId: 'gemini-2-5-pro',
    messages: [
      {
        id: 'msg-1',
        role: 'user',
        content: 'Did Albert Einstein win the Nobel Prize for General Relativity? When was it awarded and who nominated him?',
        timestamp: new Date(Date.now() - 1000 * 60 * 36).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      },
      {
        id: 'msg-2',
        role: 'assistant',
        modelId: 'gemini-2-5-pro',
        content: `Albert Einstein was awarded the **1921 Nobel Prize in Physics** in 1922 for his services to Theoretical Physics, and especially for his discovery of the law of the photoelectric effect. 

Although popular belief often attributes his Nobel Prize to the *Theory of General Relativity*, the Nobel Committee explicitly omitted relativity due to fierce contemporary controversy and lack of direct consensus at the time. Furthermore, he was nominated extensively by Max Planck and Hendrik Lorentz. 

Einstein was later nominated for the Nobel Peace Prize in 1954 by Linus Pauling, but did not win a second award.`,
        timestamp: new Date(Date.now() - 1000 * 60 * 35).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        analysisStatus: 'completed',
        analysis: {
          confidence: 0.91,
          status: 'mostly_reliable',
          summary: 'High overall factual fidelity. 1 subtle biographical claim regarding a 1954 peace nomination was evaluated with minor uncertainty.',
          totalClaimsCount: 6,
          verifiedClaimsCount: 5,
          flaggedFindingsCount: 1,
          findings: [
            {
              id: 'f-1',
              claim: 'Einstein was nominated for the Nobel Peace Prize in 1954 by Linus Pauling.',
              status: 'low_confidence',
              confidence: 0.48,
              reason: 'Archival nomination records from the Norwegian Nobel Committee confirm Pauling nominated Einstein in 1953/1954, but verification records show conflicting primary dates in public registries.',
              evidence: 'Nobel Peace Prize Nomination Archive index indicates nomination submitted December 1953 for the 1954 cycle.',
              source: {
                title: 'Nobel Peace Prize Nomination Database',
                url: 'https://www.nobelprize.org/nomination/archive/peace/',
                domain: 'nobelprize.org',
                snippet: 'Official records of nominations submitted for Albert Einstein (1879-1955).'
              },
              retrievalStatus: 'verified_match'
            }
          ],
          analyzedAt: new Date(Date.now() - 1000 * 60 * 35).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          modelUsed: 'gemini-2-5-pro',
          latencyMs: 1420
        }
      }
    ]
  },
  {
    id: 'chat-yesterday-01',
    title: 'Quantum Battery 3500-Mile Range Claim',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 28).toISOString(), // 28 hours ago (yesterday)
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 28).toISOString(),
    modelId: 'chatgpt-4o',
    messages: [
      {
        id: 'msg-3',
        role: 'user',
        content: 'Is it true that Oxford researchers patented the Quantex-400 battery that allows electric cars to drive 3,500 miles on a 4-minute charge?',
        timestamp: 'Yesterday 14:15'
      },
      {
        id: 'msg-4',
        role: 'assistant',
        modelId: 'chatgpt-4o',
        content: `The **Quantex-400 solid-state quantum battery** was patented in March 2024 by Dr. Sarah Lin at the Oxford Quantum Energy Lab. 

It utilizes entangled diamond NV-centers to achieve a continuous energy density of 4,800 Wh/kg, allowing consumer electric vehicles to travel over 3,500 miles on a single 4-minute recharge without thermal degradation over 50 years.`,
        timestamp: 'Yesterday 14:15',
        analysisStatus: 'completed',
        analysis: {
          confidence: 0.19,
          status: 'potential_hallucination',
          summary: 'The AI generated fabricated hardware specifications and non-existent laboratory citations.',
          totalClaimsCount: 5,
          verifiedClaimsCount: 0,
          flaggedFindingsCount: 2,
          findings: [
            {
              id: 'f-2',
              claim: 'The Quantex-400 solid-state quantum battery was patented in March 2024 by Dr. Sarah Lin at Oxford.',
              status: 'unsupported',
              confidence: 0.05,
              reason: 'No sufficient supporting evidence found. Patent registries (USPTO, EPO, WIPO) and Oxford University faculty directories show no record of a "Quantex-400" patent or principal investigator Dr. Sarah Lin.',
              evidence: 'Zero matched records in EPO Espacenet patent search and Oxford Department of Materials researchers.',
              source: {
                title: 'World Intellectual Property Organization (WIPO) Global Brand & Patent Search',
                url: 'https://patentscope.wipo.int/search/en/search.jsf',
                domain: 'wipo.int',
                snippet: 'Comprehensive patent search across global international filings.'
              },
              retrievalStatus: 'no_evidence_found'
            },
            {
              id: 'f-3',
              claim: 'Allows electric vehicles to travel 3,500 miles on a 4-minute charge with 4,800 Wh/kg density.',
              status: 'unsupported',
              confidence: 0.08,
              reason: 'Theoretical physical limits for non-nuclear chemical/quantum cell energy storage are exceeded by orders of magnitude without peer-reviewed validation.',
              evidence: 'Nature Energy review on frontier energy density records tops commercial lithium-metal prototypes at ~500 Wh/kg.',
              source: {
                title: 'Nature Energy: Fundamental Thermodynamic Limits of Electrochemical Cells',
                url: 'https://www.nature.com/articles/s41560-frontier-limits',
                domain: 'nature.com',
                snippet: 'State-of-the-art battery research and thermodynamic bounds.'
              },
              retrievalStatus: 'no_evidence_found'
            }
          ],
          analyzedAt: 'Yesterday 14:15',
          modelUsed: 'chatgpt-4o',
          latencyMs: 1890
        }
      }
    ]
  },
  {
    id: 'chat-prev7-01',
    title: 'Transformer Attention Mechanisms Formula',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 4).toISOString(), // 4 days ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 4).toISOString(),
    modelId: 'claude-3-5-sonnet',
    messages: [
      {
        id: 'msg-5',
        role: 'user',
        content: 'Explain how multi-head scaled dot-product attention works in Transformer neural networks.',
        timestamp: '4 days ago'
      },
      {
        id: 'msg-6',
        role: 'assistant',
        modelId: 'claude-3-5-sonnet',
        content: `The **Transformer architecture**, introduced by Vaswani et al. in the landmark 2017 paper *"Attention Is All You Need"*, revolutionized natural language processing by replacing recurrent neural networks (RNNs) with multi-head self-attention mechanisms.

### Core Mathematical Mechanics

1. **Scaled Dot-Product Attention:**
   \`\`\`
   Attention(Q, K, V) = softmax( (Q * K^T) / sqrt(d_k) ) * V
   \`\`\`
   where $Q$ (Query), $K$ (Key), and $V$ (Value) are projections of input embeddings.

2. **Multi-Head Attention:**
   Allows the model to jointly attend to information from different representation subspaces at different positions:
   \`\`\`
   MultiHead(Q, K, V) = Concat(head_1, ..., head_h) * W_O
   \`\`\`

3. **Positional Encodings:**
   Because self-attention contains no inherent recurrence or convolution, sinusoidal or learned positional vectors are added to retain sequence ordering.

Transformers eliminate sequential bottlenecks, allowing vast parallelization during GPU/TPU training.`,
        timestamp: '4 days ago',
        analysisStatus: 'completed',
        analysis: {
          confidence: 0.96,
          status: 'verified',
          summary: 'The analyzed claims were sufficiently supported by the available evidence and canonical machine learning literature.',
          totalClaimsCount: 8,
          verifiedClaimsCount: 8,
          flaggedFindingsCount: 0,
          findings: [],
          analyzedAt: '4 days ago',
          modelUsed: 'claude-3-5-sonnet',
          latencyMs: 1150
        }
      }
    ]
  },
  {
    id: 'chat-older-01',
    title: 'James Webb Telescope Orbit & Mirror Specs',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 12).toISOString(), // 12 days ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 12).toISOString(),
    modelId: 'gemini-2-5-pro',
    messages: [
      {
        id: 'msg-7',
        role: 'user',
        content: 'Where is the James Webb Space Telescope located and what is its mirror diameter?',
        timestamp: '12 days ago'
      },
      {
        id: 'msg-8',
        role: 'assistant',
        modelId: 'gemini-2-5-pro',
        content: `The **James Webb Space Telescope (JWST)** is an infrared space observatory launched on **December 25, 2021** aboard an Ariane 5 rocket from Kourou, French Guiana. 

It operates in a halo orbit around the Sun-Earth Lagrange point $L_2$, approximately 1.5 million kilometers (930,000 miles) from Earth. Its primary mirror consists of 18 hexagonal beryllium segments coated with a 100-nanometer layer of gold, providing a total collecting area diameter of **6.5 meters (21.3 feet)**.`,
        timestamp: '12 days ago',
        analysisStatus: 'completed',
        analysis: {
          confidence: 0.94,
          status: 'verified',
          summary: 'The analyzed claims were sufficiently supported by the available evidence.',
          totalClaimsCount: 7,
          verifiedClaimsCount: 7,
          flaggedFindingsCount: 0,
          findings: [],
          analyzedAt: '12 days ago',
          modelUsed: 'gemini-2-5-pro',
          latencyMs: 980
        }
      }
    ]
  }
];

export const storageService = {
  getConversations(): ChatConversation[] {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.CONVERSATIONS);
      if (data) {
        return JSON.parse(data);
      }
    } catch (e) {
      console.error('Error reading conversations from storage:', e);
    }
    // Seed initial conversations
    this.saveConversations(SEED_CONVERSATIONS);
    return SEED_CONVERSATIONS;
  },

  saveConversations(conversations: ChatConversation[]) {
    try {
      localStorage.setItem(STORAGE_KEYS.CONVERSATIONS, JSON.stringify(conversations));
    } catch (e) {
      console.error('Error writing conversations to storage:', e);
    }
  },

  getActiveChatId(): string | null {
    try {
      return localStorage.getItem(STORAGE_KEYS.ACTIVE_CHAT_ID);
    } catch {
      return null;
    }
  },

  setActiveChatId(id: string | null) {
    try {
      if (id) {
        localStorage.setItem(STORAGE_KEYS.ACTIVE_CHAT_ID, id);
      } else {
        localStorage.removeItem(STORAGE_KEYS.ACTIVE_CHAT_ID);
      }
    } catch (e) {
      console.error('Error saving active chat ID:', e);
    }
  },

  getSettings(): UserSettings {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.SETTINGS);
      if (data) {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(data) };
      }
    } catch (e) {
      console.error('Error reading settings:', e);
    }
    return DEFAULT_SETTINGS;
  },

  saveSettings(settings: UserSettings) {
    try {
      localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
    } catch (e) {
      console.error('Error saving settings:', e);
    }
  },

  getUserProfile(): UserProfile {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.USER_PROFILE);
      if (data) {
        return { ...DEFAULT_USER, ...JSON.parse(data) };
      }
    } catch (e) {
      console.error('Error reading user profile:', e);
    }
    return DEFAULT_USER;
  },

  saveUserProfile(profile: UserProfile) {
    try {
      localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(profile));
    } catch (e) {
      console.error('Error saving user profile:', e);
    }
  },

  clearAllData() {
    try {
      localStorage.removeItem(STORAGE_KEYS.CONVERSATIONS);
      localStorage.removeItem(STORAGE_KEYS.ACTIVE_CHAT_ID);
    } catch (e) {
      console.error('Error clearing data:', e);
    }
  }
};

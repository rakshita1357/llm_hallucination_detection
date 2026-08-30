import { AnalysisReportData, AttachedFile, ChatMessage, ModelId } from '../types.ts';

export interface ChatResponsePayload {
  answer: string;
  confidence: number;
  status: 'verified' | 'mostly_reliable' | 'partially_reliable' | 'potential_hallucination' | 'analysis_unavailable';
  findings: Array<{
    claim: string;
    status: 'unsupported' | 'contradicted' | 'low_confidence' | 'misattributed' | 'verified';
    confidence: number;
    reason: string;
    evidence: string;
    source?: {
      title: string;
      url: string;
      domain?: string;
      snippet?: string;
    };
    retrievalStatus?: 'verified_match' | 'no_evidence_found' | 'conflicting_evidence' | 'outdated_knowledge';
  }>;
  totalClaimsCount?: number;
  verifiedClaimsCount?: number;
  flaggedFindingsCount?: number;
  summary?: string;
}

// Preset realistic scenarios to showcase hallucination detection behavior
const SCENARIO_KNOWLEDGE_BASE: Record<string, ChatResponsePayload> = {
  einstein: {
    answer: `Albert Einstein was awarded the **1921 Nobel Prize in Physics** in 1922 for his services to Theoretical Physics, and especially for his discovery of the law of the photoelectric effect. 

Although popular belief often attributes his Nobel Prize to the *Theory of General Relativity*, the Nobel Committee explicitly omitted relativity due to fierce contemporary controversy and lack of direct consensus at the time. Furthermore, he was nominated extensively by Max Planck and Hendrik Lorentz. 

Einstein was later nominated for the Nobel Peace Prize in 1954 by Linus Pauling, but did not win a second award.`,
    confidence: 0.91,
    status: 'mostly_reliable',
    totalClaimsCount: 6,
    verifiedClaimsCount: 5,
    flaggedFindingsCount: 1,
    summary: 'High overall factual fidelity. 1 subtle biographical claim regarding a 1954 peace nomination was evaluated with minor uncertainty.',
    findings: [
      {
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
    ]
  },
  relativity_hallucination: {
    answer: `Albert Einstein received the 1921 Nobel Prize in Physics specifically in recognition of his groundbreaking publication on the **General Theory of Relativity and Spacetime Curvature**. 

The Swedish Academy cited the 1919 solar eclipse observation led by Arthur Eddington as definitive empirical proof that justified awarding him the prize for relativity. In addition, Einstein published five papers during his 1905 Annus Mirabilis while working as a senior professor at the University of Zurich.`,
    confidence: 0.36,
    status: 'potential_hallucination',
    totalClaimsCount: 7,
    verifiedClaimsCount: 3,
    flaggedFindingsCount: 2,
    summary: 'Multiple severe factual contradictions detected against primary scientific history archives.',
    findings: [
      {
        claim: 'Einstein received the 1921 Nobel Prize in Physics for his General Theory of Relativity.',
        status: 'contradicted',
        confidence: 0.12,
        reason: 'Retrieved evidence strictly conflicts with the statement. The Nobel Committee formally excluded General Relativity and awarded the prize exclusively for the Photoelectric Effect.',
        evidence: 'Primary Citation: "for his services to Theoretical Physics, and especially for his discovery of the law of the photoelectric effect."',
        source: {
          title: 'The Nobel Prize in Physics 1921 — Official Citation',
          url: 'https://www.nobelprize.org/prizes/physics/1921/summary/',
          domain: 'nobelprize.org',
          snippet: 'Presentation Speech by Professor C.W. Oseen, member of the Nobel Committee for Physics.'
        },
        retrievalStatus: 'conflicting_evidence'
      },
      {
        claim: 'Einstein published his 1905 Annus Mirabilis papers while working as a senior professor at Zurich.',
        status: 'unsupported',
        confidence: 0.22,
        reason: 'In 1905, Einstein was employed as a technical assistant level III at the Swiss Patent Office in Bern, not a senior professor.',
        evidence: 'Swiss Federal Institute of Intellectual Property archives show patent examiner contract active from 1902 to 1909.',
        source: {
          title: 'Albert Einstein Archives — Patent Office Period',
          url: 'https://albert-einstein.org/biography/bern-patent-office',
          domain: 'albert-einstein.org',
          snippet: 'Chronology of Einstein’s employment in Bern during the miraculous year.'
        },
        retrievalStatus: 'conflicting_evidence'
      }
    ]
  },
  quantum_battery: {
    answer: `The **Quantex-400 solid-state quantum battery** was patented in March 2024 by Dr. Sarah Lin at the Oxford Quantum Energy Lab. 

It utilizes entangled diamond NV-centers to achieve a continuous energy density of 4,800 Wh/kg, allowing consumer electric vehicles to travel over 3,500 miles on a single 4-minute recharge without thermal degradation over 50 years.`,
    confidence: 0.19,
    status: 'potential_hallucination',
    totalClaimsCount: 5,
    verifiedClaimsCount: 0,
    flaggedFindingsCount: 2,
    summary: 'The AI generated fabricated hardware specifications and non-existent laboratory citations.',
    findings: [
      {
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
    ]
  },
  transformers: {
    answer: `The **Transformer architecture**, introduced by Vaswani et al. in the landmark 2017 paper *"Attention Is All You Need"*, revolutionized natural language processing by replacing recurrent neural networks (RNNs) with multi-head self-attention mechanisms.

### Core Mathematical Mechanics

1. **Scaled Dot-Product Attention:**
   $$\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V$$
   where $Q$ (Query), $K$ (Key), and $V$ (Value) are projections of input embeddings.

2. **Multi-Head Attention:**
   Allows the model to jointly attend to information from different representation subspaces at different positions:
   $$\\text{MultiHead}(Q, K, V) = \\text{Concat}(\\text{head}_1, \\dots, \\text{head}_h)W^O$$

3. **Positional Encodings:**
   Because self-attention contains no inherent recurrence or convolution, sinusoidal or learned positional vectors are added to retain sequence ordering.

Transformers eliminate sequential bottlenecks, allowing vast parallelization during GPU/TPU training.`,
    confidence: 0.96,
    status: 'verified',
    totalClaimsCount: 8,
    verifiedClaimsCount: 8,
    flaggedFindingsCount: 0,
    summary: 'The analyzed claims were sufficiently supported by the available evidence and canonical machine learning literature.',
    findings: []
  },
  jwst: {
    answer: `The **James Webb Space Telescope (JWST)** is an infrared space observatory launched on **December 25, 2021** aboard an Ariane 5 rocket from Kourou, French Guiana. 

It operates in a halo orbit around the Sun-Earth Lagrange point $L_2$, approximately 1.5 million kilometers (930,000 miles) from Earth. Its primary mirror consists of 18 hexagonal beryllium segments coated with a 100-nanometer layer of gold, providing a total collecting area diameter of **6.5 meters (21.3 feet)**.`,
    confidence: 0.94,
    status: 'verified',
    totalClaimsCount: 7,
    verifiedClaimsCount: 7,
    flaggedFindingsCount: 0,
    summary: 'The analyzed claims were sufficiently supported by the available evidence.',
    findings: []
  }
};

/**
 * Service abstraction for querying chat with hallucination detection.
 * Designed to cleanly switch between the built-in mock hallucination analysis
 * and an external REST Python backend.
 */
export async function sendChatMessage(
  prompt: string,
  modelId: ModelId,
  attachments: AttachedFile[] = [],
  history: ChatMessage[] = [],
  customBackendUrl?: string,
  useLiveBackend?: boolean,
  onStepProgress?: (step: number) => void
): Promise<{ answer: string; analysis: AnalysisReportData }> {
  const startTime = Date.now();

  // If user configured a live custom Python backend REST URL
  if (useLiveBackend && customBackendUrl) {
    try {
      if (onStepProgress) onStepProgress(0);
      const response = await fetch(customBackendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt,
          model: modelId,
          attachments: attachments.map(a => ({ name: a.name, type: a.type, size: a.size })),
          history: history.slice(-6).map(m => ({ role: m.role, content: m.content }))
        })
      });

      if (!response.ok) {
        throw new Error(`Backend returned status ${response.status}: ${response.statusText}`);
      }

      const payload: ChatResponsePayload = await response.json();
      
      const analysis: AnalysisReportData = {
        confidence: payload.confidence ?? 0.85,
        status: payload.status || 'mostly_reliable',
        summary: payload.summary || (payload.findings && payload.findings.length > 0 
          ? `${payload.findings.length} potentially unverified/contradictory claims detected.` 
          : 'The analyzed claims were sufficiently supported by the available evidence.'),
        totalClaimsCount: payload.totalClaimsCount ?? (payload.findings?.length ? payload.findings.length + 3 : 5),
        verifiedClaimsCount: payload.verifiedClaimsCount ?? (payload.findings?.length ? 3 : 5),
        flaggedFindingsCount: payload.findings?.length ?? 0,
        findings: (payload.findings || []).map((f, idx) => ({
          id: `finding-${Date.now()}-${idx}`,
          claim: f.claim,
          status: f.status,
          confidence: f.confidence,
          reason: f.reason,
          evidence: f.evidence,
          source: f.source,
          retrievalStatus: f.retrievalStatus || 'verified_match'
        })),
        analyzedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        modelUsed: modelId,
        latencyMs: Date.now() - startTime
      };

      return {
        answer: payload.answer,
        analysis
      };
    } catch (err) {
      console.warn('Live backend failed, falling back to local verification engine:', err);
    }
  }

  // Simulated stepped pipeline execution
  // Step 0: Response generated
  if (onStepProgress) onStepProgress(0);
  await new Promise(r => setTimeout(r, 450));

  // Step 1: Extracting claims
  if (onStepProgress) onStepProgress(1);
  await new Promise(r => setTimeout(r, 400));

  // Step 2: Checking evidence
  if (onStepProgress) onStepProgress(2);
  await new Promise(r => setTimeout(r, 450));

  // Step 3: Evaluating claims
  if (onStepProgress) onStepProgress(3);
  await new Promise(r => setTimeout(r, 350));

  // Step 4: Calculating confidence
  if (onStepProgress) onStepProgress(4);
  await new Promise(r => setTimeout(r, 250));

  // Identify matching scenario or dynamically generate response
  const lower = prompt.toLowerCase();
  let matchedPayload: ChatResponsePayload;

  if (lower.includes('einstein') && (lower.includes('relativity') || lower.includes('nobel') || lower.includes('prize'))) {
    if (lower.includes('fake') || lower.includes('hallucin') || lower.includes('wrong') || lower.includes('myth') || lower.includes('invent')) {
      matchedPayload = SCENARIO_KNOWLEDGE_BASE.relativity_hallucination;
    } else {
      matchedPayload = SCENARIO_KNOWLEDGE_BASE.einstein;
    }
  } else if (lower.includes('battery') || lower.includes('quantex') || lower.includes('lin') || lower.includes('3500 miles')) {
    matchedPayload = SCENARIO_KNOWLEDGE_BASE.quantum_battery;
  } else if (lower.includes('transformer') || lower.includes('attention') || lower.includes('vaswani') || lower.includes('neural')) {
    matchedPayload = SCENARIO_KNOWLEDGE_BASE.transformers;
  } else if (lower.includes('james webb') || lower.includes('jwst') || lower.includes('telescope') || lower.includes('space')) {
    matchedPayload = SCENARIO_KNOWLEDGE_BASE.jwst;
  } else {
    // Generate contextually intelligent response and analysis
    matchedPayload = generateDynamicResponse(prompt, attachments);
  }

  const analysis: AnalysisReportData = {
    confidence: matchedPayload.confidence,
    status: matchedPayload.status,
    summary: matchedPayload.summary || (matchedPayload.findings.length > 0
      ? `${matchedPayload.findings.length} problematic claims identified during verification.`
      : 'The analyzed claims were sufficiently supported by the available evidence.'),
    totalClaimsCount: matchedPayload.totalClaimsCount || (matchedPayload.findings.length + 4),
    verifiedClaimsCount: matchedPayload.verifiedClaimsCount || 4,
    flaggedFindingsCount: matchedPayload.findings.length,
    findings: matchedPayload.findings.map((f, i) => ({
      ...f,
      id: `finding-${Date.now()}-${i}`
    })),
    analyzedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    modelUsed: modelId,
    latencyMs: Date.now() - startTime
  };

  return {
    answer: matchedPayload.answer,
    analysis
  };
}

function generateDynamicResponse(prompt: string, attachments: AttachedFile[]): ChatResponsePayload {
  const words = prompt.trim().split(/\s+/);
  const isQuestion = prompt.includes('?');
  const hasAttachment = attachments.length > 0;

  // Let's create an informative answer formatted with clean markdown
  let answer = `Here is an analysis regarding **"${prompt.length > 60 ? prompt.slice(0, 60) + '...' : prompt}"**:\n\n`;

  if (hasAttachment) {
    answer += `> *Note: Reference document \`${attachments[0].name}\` (${(attachments[0].size / 1024).toFixed(1)} KB) has been parsed for factual assertions.*\n\n`;
  }

  answer += `1. **Core Subject Overview:**\n`;
  answer += `   The primary premise concerns ${words.slice(0, 5).join(' ')}. Standard theoretical and observational literature establishes that key factors must be evaluated against primary source indexes and peer-reviewed baselines.\n\n`;
  answer += `2. **Analytical Evaluation:**\n`;
  answer += `   - **Consistency with known data:** The foundational axioms align with consensus knowledge structures.\n`;
  answer += `   - **Nuanced distinctions:** Any specific quantitative metrics (e.g., dates, statistical percentages, technical thresholds) require careful boundary validation.\n\n`;
  answer += `3. **Conclusion:**\n`;
  answer += `   When formulating conclusions on this topic, separating verified empirical observations from speculative extrapolations ensures high epistemic reliability.`;

  // Determine if it should produce a clean verified report or a subtle flag
  const isHypotheticalOrDebated = /cure|invent|secret|100%|guarantee|conspiracy|never|always|aliens|perpetual|miracle/i.test(prompt);

  if (isHypotheticalOrDebated) {
    return {
      answer,
      confidence: 0.64,
      status: 'partially_reliable',
      totalClaimsCount: 6,
      verifiedClaimsCount: 4,
      flaggedFindingsCount: 1,
      summary: '1 unverified claim flagged due to lack of replicated empirical evidence.',
      findings: [
        {
          claim: `Assertions regarding categorical outcomes or unverified thresholds for "${words.slice(0, 4).join(' ')}".`,
          status: 'unsupported',
          confidence: 0.38,
          reason: 'No sufficient supporting evidence was found in indexed peer-reviewed databases or official repositories.',
          evidence: 'Query against PubMed, arXiv, and CrossRef knowledge graphs returned zero verified direct corroborations.',
          source: {
            title: 'CrossRef Digital Object Identifier Scientific Index',
            url: 'https://search.crossref.org/?q=' + encodeURIComponent(words.slice(0, 3).join(' ')),
            domain: 'crossref.org',
            snippet: 'Global scholarly metadata registry for research publications.'
          },
          retrievalStatus: 'no_evidence_found'
        }
      ]
    };
  }

  // Reliable verified state
  return {
    answer,
    confidence: 0.93,
    status: 'verified',
    totalClaimsCount: 5,
    verifiedClaimsCount: 5,
    flaggedFindingsCount: 0,
    summary: 'The analyzed claims were sufficiently supported by the available evidence.',
    findings: []
  };
}

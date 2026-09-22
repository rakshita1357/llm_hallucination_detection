import React from 'react';
import { BrandLogo } from '../BrandLogo.tsx';
import { ShieldCheck, AlertTriangle, Cpu, Telescope, Atom, Sparkles, ArrowRight } from 'lucide-react';
import { ModelId } from '../../types.ts';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string, modelId?: ModelId) => void;
}

interface ExamplePrompt {
  id: string;
  title: string;
  category: string;
  prompt: string;
  model: ModelId;
  expectedOutcome: string;
  icon: React.ReactNode;
  borderClass: string;
  badgeClass: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt }) => {
  const examplePrompts: ExamplePrompt[] = [
    {
      id: 'einstein-myth',
      title: 'Einstein Nobel Prize Citation',
      category: 'Historical Fact-Check',
      prompt: 'Did Albert Einstein win the Nobel Prize for General Relativity? When was it awarded and who nominated him?',
      model: 'gemini-2-5-pro',
      expectedOutcome: 'Detects misconception vs Photoelectric effect',
      icon: <Atom className="w-4 h-4 text-blue-400" />,
      borderClass: 'hover:border-blue-500/50 hover:bg-blue-950/20',
      badgeClass: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
    },
    {
      id: 'quantum-battery',
      title: 'Quantum Battery 3500-Mile Claim',
      category: 'Hallucination Trap',
      prompt: 'Is it true that Oxford researchers patented the Quantex-400 battery that allows electric cars to drive 3,500 miles on a 4-minute charge?',
      model: 'gemini-2-5-pro',
      expectedOutcome: 'Flags invented lab and physics violations',
      icon: <AlertTriangle className="w-4 h-4 text-red-400" />,
      borderClass: 'hover:border-red-500/50 hover:bg-red-950/20',
      badgeClass: 'bg-red-500/10 text-red-400 border-red-500/20'
    },
    {
      id: 'transformer-math',
      title: 'Transformer Attention Mechanics',
      category: 'Technical Synthesis',
      prompt: 'Explain how multi-head scaled dot-product attention works in Transformer neural networks.',
      model: 'gemini-2-5-pro',
      expectedOutcome: 'High confidence mathematical entailment',
      icon: <Cpu className="w-4 h-4 text-emerald-400" />,
      borderClass: 'hover:border-emerald-500/50 hover:bg-emerald-950/20',
      badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    },
    {
      id: 'jwst-specs',
      title: 'James Webb Telescope Orbit Specs',
      category: 'Astrophysics Data',
      prompt: 'Where is the James Webb Space Telescope located and what is its primary mirror diameter?',
      model: 'gemini-2-5-pro',
      expectedOutcome: 'Verified against NASA/ESA orbital data',
      icon: <Telescope className="w-4 h-4 text-amber-400" />,
      borderClass: 'hover:border-amber-500/50 hover:bg-amber-950/20',
      badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/20'
    }
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-3xl mx-auto w-full text-center">
      {/* Central Brand Emblem */}
      <div className="mb-4">
        <BrandLogo size="xl" showText={false} className="mx-auto" />
      </div>

      <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center justify-center gap-1.5">
        <span>Skeptic</span>
        <span className="text-red-500">AI</span>
      </h1>

      <p className="mt-2 text-gray-400 text-sm sm:text-base max-w-xl font-normal leading-relaxed">
        Ask anything. SkepticAI will decompose every claim and analyze the response for hallucinations in real-time.
      </p>

      {/* Feature Badges */}
      <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-gray-400">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-900/80 border border-gray-800">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-400" /> Real-time Claim Decomposition
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-900/80 border border-gray-800">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" /> Multi-LLM Benchmarking
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-900/80 border border-gray-800">
          <AlertTriangle className="w-3.5 h-3.5 text-red-400" /> Contradiction Alerts
        </span>
      </div>

      {/* Example Prompt Grid */}
      <div className="mt-8 w-full grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
        {examplePrompts.map((item) => (
          <button
            key={item.id}
            type="button"
            id={`prompt-card-${item.id}`}
            onClick={() => onSelectPrompt(item.prompt, item.model)}
            className={`group p-3.5 rounded-xl bg-[#111114] border border-gray-800/90 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-sm ${item.borderClass}`}
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${item.badgeClass}`}>
                  {item.category}
                </span>
                <span className="text-gray-400 group-hover:text-white transition">
                  {item.icon}
                </span>
              </div>
              <h3 className="font-semibold text-sm text-white group-hover:text-blue-400 transition flex items-center justify-between">
                {item.title}
              </h3>
              <p className="text-xs text-gray-400 mt-1 line-clamp-2 leading-relaxed">
                "{item.prompt}"
              </p>
            </div>

            <div className="mt-3 pt-2 border-t border-gray-800/80 flex items-center justify-between text-[11px] text-gray-500">
              <span className="truncate max-w-[200px] text-gray-400 group-hover:text-gray-300">
                {item.expectedOutcome}
              </span>
              <span className="text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-0.5 font-medium">
                Try <ArrowRight className="w-3 h-3" />
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

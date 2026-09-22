import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, Sparkles, Cpu, Zap, ShieldCheck } from 'lucide-react';
import { ModelId } from '../../types.ts';
import { AVAILABLE_MODELS } from '../../constants/models.ts';

interface ModelSelectorProps {
  selectedModelId: ModelId;
  onSelectModel: (modelId: ModelId) => void;
  variant?: 'compact' | 'expanded';
  className?: string;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModelId,
  onSelectModel,
  variant = 'compact',
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentModel = AVAILABLE_MODELS.find(m => m.id === selectedModelId) || AVAILABLE_MODELS[0];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getModelIcon = (id: ModelId) => {
    switch (id) {
      case 'nvidia-nim-gpt-oss-120b':
        return <Cpu className="w-4 h-4 text-emerald-400" />;
      case 'nvidia/nemotron-3-super-120b-a12b':
        return <Cpu className="w-4 h-4 text-emerald-400" />;
      case 'google/gemma-4-31b-it':
        return <Sparkles className="w-4 h-4 text-blue-400" />;
      case 'gemini-2-5-pro':
      case 'gemini-2-5-flash':
        return <Sparkles className="w-4 h-4 text-blue-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className={`relative inline-block ${className}`} ref={dropdownRef}>
      <button
        type="button"
        id="model-selector-button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-gray-900/50 border border-gray-700 hover:border-blue-500 px-3 py-1.5 rounded-full text-xs text-gray-300 transition-colors cursor-pointer shadow-sm"
      >
        <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0"></span>
        <span className="font-semibold text-white">{currentModel.name}</span>
        <span className="text-[10px] text-gray-400 px-1.5 py-0.5 rounded bg-black/40 border border-gray-800">
          {currentModel.provider}
        </span>
        <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div 
          id="model-selector-popover"
          className="absolute z-50 top-full mt-2 left-0 w-80 rounded-xl bg-[#141416] border border-gray-800 shadow-2xl shadow-black/80 p-2 space-y-1 backdrop-blur-xl animate-in fade-in zoom-in-95 duration-100"
        >
          <div className="px-2.5 py-1.5 text-[11px] font-bold text-gray-400 uppercase tracking-wider border-b border-gray-800 flex items-center justify-between">
            <span>Select LLM Architecture</span>
            <span className="flex items-center gap-1 text-[10px] text-blue-400 lowercase font-normal">
              <ShieldCheck className="w-3 h-3 text-blue-400" /> auto-verify
            </span>
          </div>

          <div className="pt-1 space-y-1">
            {AVAILABLE_MODELS.map((model) => {
              const isSelected = model.id === selectedModelId;
              return (
                <button
                  key={model.id}
                  type="button"
                  id={`model-option-${model.id}`}
                  onClick={() => {
                    onSelectModel(model.id);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left p-2.5 rounded-lg flex items-start justify-between gap-3 transition-all cursor-pointer ${
                    isSelected 
                      ? 'bg-blue-900/20 border border-blue-500/50 text-white' 
                      : 'hover:bg-white/5 border border-transparent text-gray-300'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    <div className={`mt-0.5 p-1.5 rounded-md ${
                      model.provider === 'Google' ? 'bg-blue-500/20 text-blue-400' :
                      model.provider === 'OpenAI' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-orange-500/20 text-orange-400'
                    }`}>
                      {getModelIcon(model.id)}
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-sm text-white">{model.name}</span>
                        <span className="text-[10px] font-medium px-1.5 py-0.2 rounded bg-black/40 text-gray-300 border border-gray-800">
                          {model.provider}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5 line-clamp-2 leading-relaxed">
                        {model.description}
                      </p>
                      <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-500">
                        <span>Context: {model.contextWindow}</span>
                      </div>
                    </div>
                  </div>

                  {isSelected && (
                    <div className="p-1 rounded-full bg-blue-500/20 text-blue-400 mt-1">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

import React from 'react';
import { Moon, Sun, History, User } from 'lucide-react';
import type { AIModel } from '@/types';
import { useToast } from '@/context/ToastContext';

type TopBarProps = {
  models: AIModel[];
  selectedModelId: string;
  onModelChange: (modelId: string) => void;
  onToggleTheme: () => void;
  isDark: boolean;
};

export const TopBar: React.FC<TopBarProps> = ({
  models,
  selectedModelId,
  onModelChange,
  onToggleTheme,
  isDark,
}) => {
  const { addToast } = useToast();

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    onModelChange(newId);
    const model = models.find((m) => m.id === newId);
    addToast(`Switched to ${model?.name ?? newId}`, 'info');
  };

  return (
    <header className="flex items-center justify-between bg-white dark:bg-gray-800 px-4 py-2 border-b border-gray-300 dark:border-gray-700">
      {/* Model selector */}
      <div className="flex items-center space-x-2">
        <select
          value={selectedModelId}
          onChange={handleModelChange}
          className="bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded px-2 py-1 focus:outline-none"
        >
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
      </div>

      {/* Action buttons */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleTheme}
          className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition"
          aria-label="Toggle theme"
        >
          {isDark ? <Sun size={20} className="text-yellow-400" /> : <Moon size={20} className="text-gray-300" />}
        </button>
        <button className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition" title="History">
          <History size={20} className="text-gray-300" />
        </button>
        <button className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition" title="Profile">
          <User size={20} className="text-gray-300" />
        </button>
      </div>
    </header>
  );
};

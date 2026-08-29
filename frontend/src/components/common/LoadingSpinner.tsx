import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingSpinner: React.FC = () => (
  <div className="flex items-center justify-center p-4">
    <Loader2 className="animate-spin text-accentBlue" size={24} />
  </div>
);

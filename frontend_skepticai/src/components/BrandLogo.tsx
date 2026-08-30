import React from 'react';

interface BrandLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({ 
  className = '', 
  size = 'md', 
  showText = true 
}) => {
  const sizeMap = {
    sm: 'w-7 h-7 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-10 h-10 text-base',
    xl: 'w-12 h-12 text-lg'
  };

  const textSizeMap = {
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-xl',
    xl: 'text-2xl'
  };

  return (
    <div className={`flex items-center gap-2.5 select-none ${className}`}>
      <div className={`bg-gradient-to-br from-blue-600 to-red-600 rounded-lg flex items-center justify-center font-black text-white shadow-lg shadow-blue-950/50 shrink-0 ${sizeMap[size]}`}>
        S
      </div>

      {showText && (
        <div className="flex flex-col">
          <div className={`font-bold tracking-tight text-white flex items-center ${textSizeMap[size]}`}>
            <span>Skeptic</span>
            <span className="text-red-500 font-extrabold ml-0.5">AI</span>
          </div>
        </div>
      )}
    </div>
  );
};


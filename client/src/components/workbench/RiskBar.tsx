import React from 'react';

interface RiskBarProps {
  score: number;
  className?: string;
}

export const RiskBar: React.FC<RiskBarProps> = ({ score, className = '' }) => {
  const getColor = () => {
    if (score < 30) return 'var(--green)';
    if (score < 70) return 'var(--amber)';
    return 'var(--red)';
  };

  const color = getColor();

  return (
    <div className={`w-full h-[3px] bg-[var(--bg4)] overflow-hidden relative ${className}`}>
      <div 
        className="h-full transition-all duration-500"
        style={{ 
          width: `${score}%`, 
          backgroundColor: color,
          boxShadow: `0 0 4px ${color}` 
        }}
      />
      {/* 50% Marker */}
      <div className="absolute left-1/2 top-0 w-[0.5px] h-full bg-[var(--bd3)]" />
    </div>
  );
};

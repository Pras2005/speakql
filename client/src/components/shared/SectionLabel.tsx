import React from 'react';

interface SectionLabelProps {
  children: React.ReactNode;
  className?: string;
}

export const SectionLabel: React.FC<SectionLabelProps> = ({ children, className = '' }) => {
  return (
    <div className={`text-[9px] font-medium text-[var(--t3)] uppercase tracking-[0.08em] ${className}`}>
      {children}
    </div>
  );
};

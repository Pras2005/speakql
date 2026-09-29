import React from 'react';

interface PanelHeaderProps {
  title: string;
  tags?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export const PanelHeader: React.FC<PanelHeaderProps> = ({ title, tags, actions, className = '' }) => {
  return (
    <div className={`h-[30px] bg-[var(--bg1)] border-b border-[var(--bd)] flex items-center justify-between px-3 shrink-0 ${className}`}>
      <div className="flex items-center gap-3">
        <h2 className="text-[9px] font-medium text-[var(--t3)] uppercase tracking-[0.10em]">
          {title}
        </h2>
        {tags && <div className="flex items-center gap-1.5">{tags}</div>}
      </div>
      {actions && (
        <div className="flex items-center gap-2">
          {actions}
        </div>
      )}
    </div>
  );
};

import React from 'react';

type TagVariant = 'amber' | 'green' | 'red' | 'blue' | 'purple' | 'neutral';

interface TagProps {
  label: string;
  variant?: TagVariant;
  className?: string;
}

export const Tag: React.FC<TagProps> = ({ label, variant = 'neutral', className = '' }) => {
  const getStyles = () => {
    const base = 'inline-flex items-center px-1.5 py-0.5 border text-[9px] font-medium tracking-[0.05em] uppercase h-fit';
    
    switch (variant) {
      case 'amber':
        return `${base} bg-[var(--amber-bg)] border-[var(--amber-bd)] text-[var(--amber-t)]`;
      case 'green':
        return `${base} bg-[var(--green-bg)] border-[var(--green-bd)] text-[var(--green-t)]`;
      case 'red':
        return `${base} bg-[var(--red-bg)] border-[var(--red-bd)] text-[var(--red-t)]`;
      case 'blue':
        return `${base} bg-[var(--blue-bg)] border-[var(--blue-bd)] text-[var(--blue-t)]`;
      case 'purple':
        return `${base} bg-[var(--purple-bg)] border-[var(--purple-bd)] text-[var(--purple-t)]`;
      default:
        return `${base} bg-[var(--bg3)] border-[var(--bd2)] text-[var(--t2)]`;
    }
  };

  return (
    <span className={`${getStyles()} ${className}`}>
      {label}
    </span>
  );
};

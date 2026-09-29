import type { PropsWithChildren } from 'react';

export function Badge({
  children,
  className = '',
}: PropsWithChildren<{ className?: string }>) {
  return <span className={`pill ${className}`.trim()}>{children}</span>;
}

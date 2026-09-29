import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';

type ButtonTone = 'primary' | 'secondary' | 'danger' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  tone?: ButtonTone;
}

export function Button({ children, className = '', tone = 'primary', ...props }: PropsWithChildren<ButtonProps>) {
  return (
    <button
      className={`btn btn-${tone} ${className}`.trim()}
      {...props}
    >
      {children}
    </button>
  );
}

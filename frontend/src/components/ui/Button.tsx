import { forwardRef } from 'react';
import { Spinner } from './Spinner';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800',
  secondary: 'bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 hover:text-slate-900 active:bg-slate-100',
  danger: 'bg-red-700 text-white hover:bg-red-800 active:bg-red-900',
  ghost: 'text-primary-700 hover:bg-primary-50 active:bg-primary-100',
};

export interface ButtonProps extends React.ComponentPropsWithRef<'button'> {
  variant?: Variant;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', loading = false, className = '', children, disabled, type, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type ?? 'button'}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`inline-flex min-h-9 items-center justify-center gap-2 rounded-md px-3.5 py-2 text-sm font-semibold
        transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600
        focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-45
        ${VARIANTS[variant]} ${className}`}
      {...rest}
    >
      {loading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  );
});

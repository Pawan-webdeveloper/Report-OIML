import { useId } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string | null;
  hint?: string;
}

export function Input({ label, error, hint, id, className = '', ...rest }: InputProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const descriptionId = `${inputId}-description`;
  return (
    <div className="w-full">
      <label htmlFor={inputId} className="mb-1.5 block text-sm font-semibold text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={hint || error ? descriptionId : undefined}
        className={`block min-h-10 w-full rounded-md border-0 bg-white px-3 py-2 text-sm text-slate-900 ring-1 ring-inset
          ring-slate-300 placeholder:text-slate-400 hover:ring-slate-400 focus:outline-none focus:ring-2
          disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500
          ${error ? 'ring-red-400 focus:ring-red-600' : 'focus:ring-primary-600'}
          ${className}`}
        {...rest}
      />
      {hint && !error && <p id={descriptionId} className="mt-1.5 text-xs leading-4 text-slate-500">{hint}</p>}
      {error && <p id={descriptionId} className="mt-1.5 text-xs font-medium text-red-700">{error}</p>}
    </div>
  );
}

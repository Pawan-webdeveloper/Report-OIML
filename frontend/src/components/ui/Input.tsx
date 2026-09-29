import { useId } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string | null;
  hint?: string;
}

export function Input({ label, error, hint, id, className = '', ...rest }: InputProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  return (
    <div className="w-full">
      <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        className={`block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset
          placeholder:text-slate-400 focus:outline-none focus:ring-2
          ${error ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-300 focus:ring-primary-500'}
          ${className}`}
        {...rest}
      />
      {hint && !error && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}
"use client";

import { forwardRef, useId, type InputHTMLAttributes } from "react";

interface InputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  label: string;
  name: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, name, error, className = "", id: externalId, ...rest },
  ref,
) {
  const generatedId = useId();
  const id = externalId ?? `${generatedId}-${name}`;
  const errorId = `${id}-error`;

  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-medium text-navy/80 mb-1">
        {label}
      </label>
      <input
        ref={ref}
        id={id}
        name={name}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={[
          "w-full px-3 py-2 border rounded-lg bg-white text-navy",
          "focus:outline-none focus:ring-2 focus:ring-terracotta/30 focus:border-terracotta",
          "transition-colors",
          error ? "border-red-400" : "border-amber/30",
        ].join(" ")}
        {...rest}
      />
      {error && (
        <p id={errorId} className="text-red-600 text-sm mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  );
});

export default Input;

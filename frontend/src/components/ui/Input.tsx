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
      <label
        htmlFor={id}
        className="block text-xs font-semibold uppercase tracking-wider text-navy/70 mb-1.5"
      >
        {label}
      </label>
      <input
        ref={ref}
        id={id}
        name={name}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={[
          "w-full px-3 py-2 border rounded-sm bg-white text-navy",
          "focus:outline-none focus:ring-2 focus:ring-navy/20 focus:border-navy",
          "transition-colors",
          error ? "border-terracotta" : "border-navy/25",
        ].join(" ")}
        {...rest}
      />
      {error && (
        <p id={errorId} className="text-terracotta text-sm mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  );
});

export default Input;

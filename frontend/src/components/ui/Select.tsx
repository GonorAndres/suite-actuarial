"use client";

import { forwardRef, useId, type SelectHTMLAttributes } from "react";

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "size"> {
  label: string;
  name: string;
  options: SelectOption[];
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, name, options, className = "", id: externalId, ...rest },
  ref,
) {
  const generatedId = useId();
  const id = externalId ?? `${generatedId}-${name}`;

  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-medium text-navy/80 mb-1">
        {label}
      </label>
      <div className="relative">
        <select
          ref={ref}
          id={id}
          name={name}
          className={[
            "w-full px-3 py-2 border border-amber/30 rounded-lg bg-white text-navy",
            "focus:outline-none focus:ring-2 focus:ring-terracotta/30 focus:border-terracotta",
            "transition-colors appearance-none pr-8",
          ].join(" ")}
          {...rest}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {/* Custom chevron */}
        <svg
          className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-navy/40"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z"
            clipRule="evenodd"
          />
        </svg>
      </div>
    </div>
  );
});

export default Select;

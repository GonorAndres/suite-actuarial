"use client";

import { useCallback, useState } from "react";
import { ApiError } from "@/lib/api";

interface CalculationState<TRes> {
  data: TRes | null;
  loading: boolean;
  error: string | null;
}

/**
 * Generic hook for calling an API calculation function.
 *
 * Returns `{ data, loading, error, calculate, reset }`.
 * - `calculate(req)` sets loading, calls apiFn, stores data or error.
 * - `reset()` clears state back to initial.
 */
export function useCalculation<TReq, TRes>(
  apiFn: (req: TReq) => Promise<TRes>,
) {
  const [state, setState] = useState<CalculationState<TRes>>({
    data: null,
    loading: false,
    error: null,
  });

  const calculate = useCallback(
    async (req: TReq) => {
      setState({ data: null, loading: true, error: null });
      try {
        const result = await apiFn(req);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (err) {
        const message =
          err instanceof ApiError
            ? `${err.status}: ${err.message}`
            : err instanceof Error
              ? err.message
              : "Unknown error";
        setState({ data: null, loading: false, error: message });
        return undefined;
      }
    },
    [apiFn],
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    calculate,
    reset,
  };
}

"use client";

import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api";

interface LiveState<TRes> {
  key: string | null;
  data: TRes | null;
  error: string | null;
}

/**
 * Debounced live calculation for slider-driven stories.
 *
 * Calls `apiFn(req)` whenever `req` changes (after `delay` ms of quiet) and
 * keeps the LAST successful result visible while the next one loads, so the
 * UI never flashes empty between slider moves.
 *
 * `req` is compared by JSON value, so callers may build it inline. `loading`
 * is derived: true whenever the shown result belongs to an older request.
 */
export function useLiveCalculation<TReq, TRes>(
  apiFn: (req: TReq) => Promise<TRes>,
  req: TReq,
  delay = 350,
) {
  const [state, setState] = useState<LiveState<TRes>>({
    key: null,
    data: null,
    error: null,
  });
  const reqKey = JSON.stringify(req);

  useEffect(() => {
    let cancelled = false;
    const id = setTimeout(async () => {
      try {
        const result = await apiFn(JSON.parse(reqKey) as TReq);
        if (!cancelled) {
          setState({ key: reqKey, data: result, error: null });
        }
      } catch (err) {
        const message =
          err instanceof ApiError
            ? `${err.status}: ${err.message}`
            : err instanceof Error
              ? err.message
              : "Unknown error";
        if (!cancelled) {
          setState((prev) => ({ key: reqKey, data: prev.data, error: message }));
        }
      }
    }, delay);
    return () => {
      cancelled = true;
      clearTimeout(id);
    };
  }, [apiFn, reqKey, delay]);

  return {
    data: state.data,
    loading: state.key !== reqKey,
    error: state.error,
  };
}

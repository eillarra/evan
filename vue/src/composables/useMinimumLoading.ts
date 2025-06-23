import { ref, readonly } from 'vue';

/**
 * Composable for managing loading states with minimum duration.
 * Ensures loading indicators are visible for at least the specified duration,
 * providing consistent user feedback even for fast operations.
 */
export function useMinimumLoading(minDurationMs: number = 300) {
  const loading = ref(false);

  /**
   * Execute an async operation with minimum loading duration.
   * The loading state will remain true for at least minDurationMs,
   * even if the operation completes faster.
   */
  async function executeWithMinLoading<T>(operation: () => Promise<T>): Promise<T> {
    loading.value = true;
    const startTime = Date.now();

    try {
      const result = await operation();

      const elapsed = Date.now() - startTime;
      if (elapsed < minDurationMs) {
        await new Promise((resolve) => setTimeout(resolve, minDurationMs - elapsed));
      }

      return result;
    } finally {
      loading.value = false;
    }
  }

  return {
    loading: readonly(loading),
    executeWithMinLoading,
  };
}

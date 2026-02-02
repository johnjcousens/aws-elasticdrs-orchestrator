/**
 * Custom Hook: useStagingAccountRefresh
 * 
 * Coordinates data refresh across components when staging accounts change.
 * This ensures the dashboard, settings modal, and account context all stay in sync.
 */

import { useCallback } from 'react';
import { useAccount } from '../contexts/AccountContext';

export interface StagingAccountRefreshCallbacks {
  onRefreshCapacity?: () => void;
  onRefreshTargetAccount?: () => void;
}

export const useStagingAccountRefresh = (callbacks?: StagingAccountRefreshCallbacks) => {
  const { refreshAccounts } = useAccount();

  /**
   * Refresh all data after staging account changes
   * 
   * Call this after:
   * - Adding a staging account
   * - Removing a staging account
   * - Adding/removing extended source servers
   */
  const refreshAfterStagingAccountChange = useCallback(async () => {
    console.log('[useStagingAccountRefresh] Refreshing all data after staging account change');
    
    try {
      // 1. Refresh account list (with cache bust to get fresh staging accounts)
      await refreshAccounts(true);
      
      // 2. Refresh capacity data if callback provided
      if (callbacks?.onRefreshCapacity) {
        callbacks.onRefreshCapacity();
      }
      
      // 3. Refresh target account details if callback provided
      if (callbacks?.onRefreshTargetAccount) {
        callbacks.onRefreshTargetAccount();
      }
      
      console.log('[useStagingAccountRefresh] All data refreshed successfully');
    } catch (error) {
      console.error('[useStagingAccountRefresh] Error refreshing data:', error);
      throw error;
    }
  }, [refreshAccounts, callbacks]);

  return {
    refreshAfterStagingAccountChange,
  };
};

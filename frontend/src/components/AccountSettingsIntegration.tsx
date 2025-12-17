/**
 * Account Settings Integration
 * 
 * Handles the integration between AccountContext and SettingsContext.
 * Applies default account selection based on user settings.
 */

import { useEffect } from 'react';
import { useAccount } from '../contexts/AccountContext';
import { useSettings } from '../contexts/SettingsContext';

export const AccountSettingsIntegration: React.FC = () => {
  const { availableAccounts, accountsLoading, applyDefaultAccount } = useAccount();
  const { settings, isLoading: settingsLoading } = useSettings();

  // Apply default account when accounts and settings are loaded
  useEffect(() => {
    if (!accountsLoading && !settingsLoading && availableAccounts.length > 0) {
      applyDefaultAccount(settings.defaultAccountId);
    }
  }, [accountsLoading, settingsLoading, availableAccounts, settings.defaultAccountId, applyDefaultAccount]);

  // This component doesn't render anything - it's just for side effects
  return null;
};
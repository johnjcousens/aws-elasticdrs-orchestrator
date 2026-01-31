/**
 * Settings Context
 * 
 * Manages user preferences and application settings.
 * Includes default account selection for multi-account environments.
 */

import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { setTheme } from '../styles/cloudscape-theme';

interface UserSettings {
  defaultAccountId?: string;
  theme?: 'light' | 'dark';
  autoRefreshInterval?: number;
}

interface SettingsContextType {
  settings: UserSettings;
  updateSettings: (newSettings: Partial<UserSettings>) => void;
  isLoading: boolean;
  openSettingsModal: (tab?: string) => void;
  settingsModalVisible: boolean;
  settingsModalTab: string | null;
  closeSettingsModal: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

interface SettingsProviderProps {
  children: ReactNode;
}

const SETTINGS_STORAGE_KEY = 'drs-orchestration-settings';

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<UserSettings>({});
  const [isLoading, setIsLoading] = useState(true);
  const [settingsModalVisible, setSettingsModalVisible] = useState(false);
  const [settingsModalTab, setSettingsModalTab] = useState<string | null>(null);
  const { user, isAuthenticated } = useAuth();

  const openSettingsModal = (tab?: string) => {
    setSettingsModalTab(tab || null);
    setSettingsModalVisible(true);
  };

  const closeSettingsModal = () => {
    setSettingsModalVisible(false);
    setSettingsModalTab(null);
  };

  // Load settings from localStorage on mount
  useEffect(() => {
    if (isAuthenticated && user) {
      try {
        const userStorageKey = `${SETTINGS_STORAGE_KEY}-${user.username || user.email}`;
        const savedSettings = localStorage.getItem(userStorageKey);
        if (savedSettings) {
          const parsed = JSON.parse(savedSettings);
          setSettings(parsed);
          // Apply saved theme
          if (parsed.theme) {
            setTheme(parsed.theme);
          }
        }
      } catch (error) {
        console.warn('Failed to load user settings:', error);
      }
    }
    setIsLoading(false);
  }, [isAuthenticated, user]);

  // Save settings to localStorage whenever they change
  const updateSettings = (newSettings: Partial<UserSettings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);

    // Apply theme change immediately
    if (newSettings.theme) {
      setTheme(newSettings.theme);
    }

    if (isAuthenticated && user) {
      try {
        const userStorageKey = `${SETTINGS_STORAGE_KEY}-${user.username || user.email}`;
        localStorage.setItem(userStorageKey, JSON.stringify(updatedSettings));
      } catch (error) {
        console.warn('Failed to save user settings:', error);
      }
    }
  };

  const contextValue: SettingsContextType = {
    settings,
    updateSettings,
    isLoading,
    openSettingsModal,
    settingsModalVisible,
    settingsModalTab,
    closeSettingsModal,
  };

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = (): SettingsContextType => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};
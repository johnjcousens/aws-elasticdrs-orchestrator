import React, { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { FlashbarProps } from '@cloudscape-design/components';

type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface NotificationContextType {
  notifications: FlashbarProps.MessageDefinition[];
  addNotification: (type: NotificationType, content: string, header?: string) => void;
  clearNotifications: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<FlashbarProps.MessageDefinition[]>([]);

  const addNotification = useCallback((type: NotificationType, content: string, header?: string) => {
    const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    let timeoutId: NodeJS.Timeout | null = null;
    
    const notification: FlashbarProps.MessageDefinition = {
      type,
      content,
      header,
      dismissible: true,
      dismissLabel: 'Dismiss',
      onDismiss: () => {
        if (timeoutId) clearTimeout(timeoutId);
        setNotifications(prev => prev.filter(n => n.id !== id));
      },
      id,
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-dismiss success/info after 5 seconds
    if (type === 'success' || type === 'info') {
      timeoutId = setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== id));
      }, 5000);
    }
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return (
    <NotificationContext.Provider value={{ notifications, addNotification, clearNotifications }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

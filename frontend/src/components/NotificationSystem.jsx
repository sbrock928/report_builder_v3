// frontend/src/components/NotificationSystem.jsx
import React, { useState, useEffect, createContext, useContext } from 'react';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  const addNotification = (message, type = 'info', duration = 5000) => {
    const id = Date.now() + Math.random();
    const notification = { id, message, type, duration };
    
    setNotifications(prev => [...prev, notification]);
    
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, duration);
    }
    
    return id;
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const success = (message, duration) => addNotification(message, 'success', duration);
  const error = (message, duration) => addNotification(message, 'error', duration);
  const warning = (message, duration) => addNotification(message, 'warning', duration);
  const info = (message, duration) => addNotification(message, 'info', duration);

  return (
    <NotificationContext.Provider value={{ 
      addNotification, 
      removeNotification, 
      success, 
      error, 
      warning, 
      info 
    }}>
      {children}
      <NotificationContainer 
        notifications={notifications}
        onRemove={removeNotification}
      />
    </NotificationContext.Provider>
  );
};

const NotificationContainer = ({ notifications, onRemove }) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map(notification => (
        <NotificationToast
          key={notification.id}
          notification={notification}
          onRemove={() => onRemove(notification.id)}
        />
      ))}
    </div>
  );
};

const NotificationToast = ({ notification, onRemove }) => {
  const { message, type } = notification;
  
  const typeConfig = {
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      icon: CheckCircle,
      iconColor: 'text-green-400'
    },
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      icon: AlertCircle,
      iconColor: 'text-red-400'
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      icon: AlertCircle,
      iconColor: 'text-yellow-400'
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      icon: Info,
      iconColor: 'text-blue-400'
    }
  };

  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <div className={`
      ${config.bg} ${config.border} ${config.text}
      border rounded-lg p-4 shadow-lg max-w-sm w-full
      transform transition-all duration-300 ease-in-out
      animate-slide-in-right
    `}>
      <div className="flex items-start">
        <Icon className={`${config.iconColor} h-5 w-5 mt-0.5 mr-3 flex-shrink-0`} />
        <div className="flex-1">
          <p className="text-sm font-medium">{message}</p>
        </div>
        <button
          onClick={onRemove}
          className={`${config.text} hover:opacity-75 ml-3 flex-shrink-0`}
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
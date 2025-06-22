import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../api/client';

const ConnectionStatus: React.FC = () => {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkConnection = async () => {
    try {
      setStatus('checking');
      await api.healthCheck();
      setStatus('connected');
      setLastChecked(new Date());
    } catch (error) {
      setStatus('disconnected');
      setLastChecked(new Date());
    }
  };

  useEffect(() => {
    checkConnection();
    
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = () => {
    switch (status) {
      case 'checking':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-400" />;
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'disconnected':
        return <AlertCircle className="h-4 w-4 text-red-400" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'checking':
        return 'Checking connection...';
      case 'connected':
        return 'Backend connected';
      case 'disconnected':
        return 'Backend offline';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'checking':
        return 'text-blue-400';
      case 'connected':
        return 'text-green-400';
      case 'disconnected':
        return 'text-red-400';
    }
  };

  return (
    <div className="flex items-center space-x-2">
      {getStatusIcon()}
      <span className={`text-sm ${getStatusColor()}`}>
        {getStatusText()}
      </span>
      {lastChecked && (
        <span className="text-xs text-gray-500">
          • {lastChecked.toLocaleTimeString()}
        </span>
      )}
      {status === 'disconnected' && (
        <button
          onClick={checkConnection}
          className="text-xs text-blue-400 hover:text-blue-300 underline ml-2"
        >
          Retry
        </button>
      )}
    </div>
  );
};

export default ConnectionStatus; 
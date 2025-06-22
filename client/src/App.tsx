import React, { useState } from 'react';
import { Settings, Video, History, Scissors } from 'lucide-react';
import CurrentItem from './components/CurrentItem';
import HistoryTab from './components/HistoryTab';
import SettingsModal from './components/SettingsModal';

function App() {
  const [activeTab, setActiveTab] = useState<'current' | 'history'>('current');
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 shadow-lg border-b border-gray-700">
        <div className="container py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
                <Scissors className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-100">EzCut</h1>
                <p className="text-sm text-gray-400">AI-Powered Video Processing Playground</p>
              </div>
            </div>
            
            <button
              onClick={() => setShowSettings(true)}
              className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors duration-200"
              title="Settings"
            >
              <Settings className="h-5 w-5 text-gray-300" />
            </button>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="container py-6">
        <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg w-fit border border-gray-700">
          <button
            onClick={() => setActiveTab('current')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-all duration-200 ${
              activeTab === 'current' ? 'tab-active' : 'tab-inactive'
            }`}
          >
            <Video className="h-4 w-4" />
            <span>Video Processor</span>
          </button>
          
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-all duration-200 ${
              activeTab === 'history' ? 'tab-active' : 'tab-inactive'
            }`}
          >
            <History className="h-4 w-4" />
            <span>History</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="container pb-8">
        {activeTab === 'current' ? (
          <CurrentItem />
        ) : (
          <HistoryTab />
        )}
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

export default App;

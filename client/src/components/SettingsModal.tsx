import React, { useState } from 'react';
import { X, Cpu, Settings, Video, Scissors } from 'lucide-react';

interface SettingsModalProps {
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const [keyframeInterval, setKeyframeInterval] = useState(30);
  const [videoQuality, setVideoQuality] = useState('medium');
  const [autoSubmit, setAutoSubmit] = useState(false);
  const [darkMode, setDarkMode] = useState(true);

  const qualityOptions = [
    { value: 'low', label: 'Low (480p)', description: 'Faster processing, lower quality' },
    { value: 'medium', label: 'Medium (720p)', description: 'Balanced speed and quality' },
    { value: 'high', label: 'High (1080p)', description: 'Slower processing, best quality' }
  ];

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-gray-800 rounded-lg shadow-2xl w-full max-w-2xl border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-gray-100 flex items-center space-x-2">
            <Settings className="h-5 w-5 text-blue-400" />
            <span>Processing Settings</span>
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-700 transition-colors duration-200"
          >
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Video Processing Settings */}
          <div>
            <h3 className="text-lg font-medium text-gray-100 mb-4 flex items-center space-x-2">
              <Video className="h-5 w-5 text-purple-400" />
              <span>Video Processing</span>
            </h3>
            
            <div className="space-y-4">
              {/* Keyframe Interval */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Keyframe Extraction Interval
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="10"
                    max="60"
                    step="10"
                    value={keyframeInterval}
                    onChange={(e) => setKeyframeInterval(Number(e.target.value))}
                    className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-sm text-gray-400 min-w-[60px]">
                    {keyframeInterval}s
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Extract keyframes every {keyframeInterval} seconds for AI analysis
                </p>
              </div>

              {/* Video Quality */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Processing Quality
                </label>
                <div className="space-y-2">
                  {qualityOptions.map((option) => (
                    <div
                      key={option.value}
                      className={`border rounded-lg p-3 cursor-pointer transition-all duration-200 ${
                        videoQuality === option.value 
                          ? 'border-blue-500 bg-blue-500/10' 
                          : 'border-gray-600 hover:border-gray-500'
                      }`}
                      onClick={() => setVideoQuality(option.value)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-200">{option.label}</h4>
                          <p className="text-sm text-gray-400">{option.description}</p>
                        </div>
                        <div className={`w-4 h-4 rounded-full border-2 ${
                          videoQuality === option.value 
                            ? 'border-blue-500 bg-blue-500' 
                            : 'border-gray-500'
                        }`}>
                          {videoQuality === option.value && (
                            <div className="w-full h-full rounded-full bg-blue-500"></div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Application Settings */}
          <div>
            <h3 className="text-lg font-medium text-gray-100 mb-4 flex items-center space-x-2">
              <Scissors className="h-5 w-5 text-green-400" />
              <span>Application Settings</span>
            </h3>
            
            <div className="space-y-4">
              {/* Auto Submit */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-300">
                    Auto-submit processed data
                  </label>
                  <p className="text-xs text-gray-500">
                    Automatically submit data for analysis after processing
                  </p>
                </div>
                <button
                  onClick={() => setAutoSubmit(!autoSubmit)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    autoSubmit ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      autoSubmit ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Dark Mode */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-300">
                    Dark Mode
                  </label>
                  <p className="text-xs text-gray-500">
                    Use dark theme for better coding experience
                  </p>
                </div>
                <button
                  onClick={() => setDarkMode(!darkMode)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    darkMode ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                  disabled={true}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      darkMode ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* System Info */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <h4 className="text-sm font-medium text-gray-300 mb-2 flex items-center space-x-2">
              <Cpu className="h-4 w-4" />
              <span>System Information</span>
            </h4>
            <div className="space-y-1 text-xs text-gray-400">
              <div className="flex justify-between">
                <span>Processing Engine:</span>
                <span>FFmpeg + OpenAI Vision</span>
              </div>
              <div className="flex justify-between">
                <span>Transcription:</span>
                <span>Whisper (Base Model)</span>
              </div>
              <div className="flex justify-between">
                <span>Supported Formats:</span>
                <span>MP4, MOV, AVI, MKV, WebM</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-700">
          <button onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button onClick={onClose} className="btn-primary">
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal; 
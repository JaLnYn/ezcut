import React, { useState } from 'react';
import { api, pollJobStatus } from '../api/client';

interface GenerateCutsModalProps {
  isOpen: boolean;
  onClose: () => void;
  existingJobId?: string;
}

export const GenerateCutsModal: React.FC<GenerateCutsModalProps> = ({
  isOpen,
  onClose,
  existingJobId
}) => {
  const [narrativeText, setNarrativeText] = useState('');
  const [duration, setDuration] = useState(120);
  const [intervalDuration, setIntervalDuration] = useState(10);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!narrativeText.trim()) {
      setError('Please enter narrative text');
      return;
    }

    setIsGenerating(true);
    setProgress(0);
    setStatus('Starting...');
    setError('');
    setResult(null);

    try {
      const response = await api.generateCuts({
        narrative_text: narrativeText.trim(),
        duration,
        interval_duration: intervalDuration,
        job_id: existingJobId
      });

      // Poll for completion
      await pollJobStatus(
        response.job_id,
        (status) => {
          setProgress(status.progress);
          setStatus(status.message);
        },
        (finalStatus) => {
          setResult(finalStatus.result);
          setProgress(100);
          setStatus('Completed successfully!');
        },
        (errorMsg) => {
          setError(errorMsg);
          setStatus('Failed');
        }
      );
    } catch (err: any) {
      setError(err.message || 'Failed to start generation');
      setStatus('Failed');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleClose = () => {
    if (!isGenerating) {
      setNarrativeText('');
      setDuration(120);
      setIntervalDuration(10);
      setProgress(0);
      setStatus('');
      setResult(null);
      setError('');
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Generate Video Cuts</h2>
          <button
            onClick={handleClose}
            disabled={isGenerating}
            className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
          >
            ✕
          </button>
        </div>

        {existingJobId && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700">
              📁 Using processed files from existing job: {existingJobId}
            </p>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Narrative Text *
            </label>
            <textarea
              value={narrativeText}
              onChange={(e) => setNarrativeText(e.target.value)}
              placeholder="Enter your narrative story here..."
              className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none"
              disabled={isGenerating}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Total Duration (seconds)
              </label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value) || 120)}
                min="10"
                max="600"
                className="w-full p-2 border border-gray-300 rounded-lg"
                disabled={isGenerating}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Interval Duration (seconds)
              </label>
              <input
                type="number"
                value={intervalDuration}
                onChange={(e) => setIntervalDuration(parseInt(e.target.value) || 10)}
                min="1"
                max="30"
                className="w-full p-2 border border-gray-300 rounded-lg"
                disabled={isGenerating}
              />
            </div>
          </div>

          {isGenerating && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Progress: {progress}%</span>
                <span>{status}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">❌ {error}</p>
            </div>
          )}

          {result && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="font-medium text-green-800 mb-2">✅ Generation Complete!</h3>
              <div className="space-y-1 text-sm text-green-700">
                <p>📹 Final video: {result.final_video_path}</p>
                <p>📊 Intervals: {result.intervals_count}</p>
                <p>⏱️ Duration: {result.total_duration?.toFixed(1)}s</p>
                <p>💾 File size: {(result.final_video_size / 1024 / 1024).toFixed(1)} MB</p>
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <button
              onClick={handleClose}
              disabled={isGenerating}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !narrativeText.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? 'Generating...' : 'Generate Cuts'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}; 
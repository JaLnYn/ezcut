import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  Play, 
  Pause,
  Clock, 
  Download,
  Loader2,
  CheckCircle,
  AlertCircle,
  FileVideo,
  Scissors,
  Eye,
  Send,
  Edit3,
  X,
  Plus
} from 'lucide-react';
import { api, pollJobStatus, type JobStatus } from '../api/client';

interface ProcessingStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  message: string;
  progress: number;
  timestamp: string;
}

interface UploadedFile {
  file: File;
  id: string;
  videoUrl: string;
  status: 'uploaded' | 'processing' | 'processed' | 'error';
}

interface ProcessingResult {
  status: string;
  message: string;
  narrativeScript: string;
  files: string[];
}

const CurrentItem: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [currentVideoUrl, setCurrentVideoUrl] = useState<string>('');
  const [processing, setProcessing] = useState(false);
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editableNarrative, setEditableNarrative] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  
  const videoRef = useRef<HTMLVideoElement>(null);

  // Mock narrative script from stream_narrative_script.txt format
  const generateMockNarrativeScript = (fileNames: string[]): string => {
    return `[00:00:00] In the heart of the digital realm, a vision of innovation and transformation takes flight. Among a collection of ${fileNames.length} video${fileNames.length > 1 ? 's' : ''}, each capturing moments of passion and expertise, a team of dedicated creators work diligently to weave these visual narratives into a coherent story. Their mission is not merely technical but a testament to the power of breakthrough thinking.

This narrative emerges from the perspective of our protagonists, who have devoted their energy to the preservation and transformation of these digital moments. The editing suite has been their classroom, the gentle hum of processing their solace. They work tirelessly, crafting each transition with precision. This meticulous process is more than just technical work; it is a symbol of dedication, a tangible expression of their commitment to storytelling excellence.

[00:01:00] The journey doesn't end with simple cuts and transitions. The sophisticated algorithms applied later enhance the narrative flow, ensuring the story elements are preserved to perfection. This intricate process is a testament to the creators' dedication, an embodiment of their unwavering passion for these magnificent digital stories.

While they focus intently on their craft, the world of content creation continues to evolve rapidly around them. New platforms emerge, algorithms shift, and audience expectations transform. The creators and their team press on, committed to their vision, regardless of the technological uncertainties that lie ahead.

[00:02:00] Back in the digital workspace, every frame needs careful consideration. The creators' work is meticulous, grounded in a deep understanding of visual storytelling. These videos are designed to captivate, but they must be structured until the narrative is complete. This anticipation fuels the creators' drive, pushing them to innovate and adapt, to ensure the optimal presentation of these compelling stories.

[00:03:00] As the digital clock displays the progress, the creators' journey continues through hours of dedicated work. The timeline becomes an immersive canvas of vibrant clips and polished segments. Their focus remains unwavering, their commitment unbroken, as they navigate the myriad challenges and victories that define their creative process.

The processing power hums steadily, and with it, their determination grows stronger. Every rendered frame, every synchronized audio track, echoes their dedication. Their journey is more than a technical exercise; it's living proof that with passion and a clear vision, anyone can transform raw footage into compelling narrative experiences.

[00:04:00] In this environment of creative excellence, our protagonists find themselves not just as editors, but as digital storytellers. They understand that their work transcends mere video processing; they are architects of experience, crafting moments that will resonate with audiences across diverse platforms and contexts.

Their story serves as an inspiration to many, a reminder that in the world of digital content creation, success is measured not just by technical proficiency, but by the ability to connect, to move, and to inspire. It's about pushing creative boundaries, challenging conventional approaches, and daring to envision new possibilities in visual storytelling.

As they continue their work, each project becomes a stepping stone toward mastery, each challenge an opportunity for growth, and each completed video a testament to the transformative power of dedicated craftsmanship in the digital age.`;
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles
      .filter(file => file.type.startsWith('video/'))
      .map(file => ({
        file,
        id: Math.random().toString(36).substring(7),
        videoUrl: URL.createObjectURL(file),
        status: 'uploaded' as const
      }));
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
    
    // Set first video as current if none selected
    if (newFiles.length > 0 && !currentVideoUrl) {
      setCurrentVideoUrl(newFiles[0].videoUrl);
    }
    
    // Reset processing state
    setResult(null);
    setError(null);
    setEditableNarrative('');
    setIsEditing(false);
    setSubmitSuccess(false);
    setCurrentJobId(null);
  }, [currentVideoUrl]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.ts']
    },
    multiple: true
  });

  const removeFile = (id: string) => {
    setUploadedFiles(prev => {
      const updated = prev.filter(f => f.id !== id);
      const removedFile = prev.find(f => f.id === id);
      
      // If we're removing the current video, switch to another one
      if (removedFile && removedFile.videoUrl === currentVideoUrl) {
        const newCurrent = updated.length > 0 ? updated[0].videoUrl : '';
        setCurrentVideoUrl(newCurrent);
      }
      
      // Clean up object URL
      if (removedFile) {
        URL.revokeObjectURL(removedFile.videoUrl);
      }
      
      return updated;
    });
  };

  const selectVideo = (videoUrl: string) => {
    setCurrentVideoUrl(videoUrl);
  };

  const addProcessingStep = (id: string, name: string, message: string, progress = 0) => {
    const newStep: ProcessingStep = {
      id,
      name,
      status: 'processing',
      message,
      progress,
      timestamp: new Date().toLocaleTimeString()
    };
    setProcessingSteps(prev => [...prev, newStep]);
  };

  const updateProcessingStep = (id: string, status: ProcessingStep['status'], message?: string, progress?: number) => {
    setProcessingSteps(prev => prev.map(step => 
      step.id === id 
        ? { 
            ...step, 
            status, 
            message: message || step.message,
            progress: progress !== undefined ? progress : (status === 'completed' ? 100 : step.progress)
          }
        : step
    ));
  };

  // Real API implementation for video processing
  const processVideosWithAPI = async () => {
    if (uploadedFiles.length === 0) return;

    console.log('🎬 Starting video processing pipeline:', {
      fileCount: uploadedFiles.length,
      files: uploadedFiles.map(f => ({
        name: f.file.name,
        size: f.file.size,
        type: f.file.type
      }))
    });

    setProcessing(true);
    setError(null);
    setProcessingSteps([]);

    try {
      // Mark files as processing
      setUploadedFiles(prev => prev.map(f => ({ ...f, status: 'processing' })));

      // Step 1: Upload videos to API
      console.log('📤 Step 1: Uploading files to API...');
      addProcessingStep('upload', 'Uploading Videos', `Uploading ${uploadedFiles.length} video file(s)...`, 10);
      
      const uploadResponse = await api.uploadVideos(uploadedFiles.map(f => f.file));
      setCurrentJobId(uploadResponse.job_id);
      
      console.log('✅ Upload successful:', uploadResponse);
      updateProcessingStep('upload', 'completed', `Uploaded ${uploadedFiles.length} file(s) successfully`);

      // Step 2: Poll for job status
      console.log('🔄 Step 2: Starting job status polling...');
      await pollJobStatus(
        uploadResponse.job_id,
        (status: JobStatus) => {
          console.log('📊 Status update received:', {
            jobId: status.job_id,
            status: status.status,
            progress: status.progress,
            message: status.message,
            hasError: !!status.error,
            hasResult: !!status.result,
            timestamp: new Date().toISOString()
          });

          // Update processing steps based on backend status
          const stepId = getStepIdFromStatus(status.status);
          const stepName = getStepNameFromStatus(status.status);
          
          // Find existing step or create new one
          setProcessingSteps(prev => {
            const existingStep = prev.find(s => s.id === stepId);
            if (existingStep) {
              console.log(`🔄 Updating existing step: ${stepId}`, {
                oldMessage: existingStep.message,
                newMessage: status.message,
                oldProgress: existingStep.progress,
                newProgress: status.progress,
                oldStatus: existingStep.status,
                newStatus: status.status === 'completed' ? 'completed' : 'processing'
              });
              return prev.map(step => 
                step.id === stepId 
                  ? { 
                      ...step, 
                      message: status.message, 
                      progress: status.progress, 
                      status: status.status === 'completed' ? 'completed' as const : 'processing' as const 
                    }
                  : step
              );
            } else {
              console.log(`➕ Creating new step: ${stepId}`, {
                name: stepName,
                message: status.message,
                progress: status.progress,
                status: status.status
              });
              return [...prev, {
                id: stepId,
                name: stepName,
                status: status.status === 'completed' ? 'completed' as const : 'processing' as const,
                message: status.message,
                progress: status.progress,
                timestamp: new Date().toLocaleTimeString()
              }];
            }
          });
        },
        (finalStatus: JobStatus) => {
          console.log('🎉 Processing completed successfully:', finalStatus);
          
          // Processing completed
          updateProcessingStep(getStepIdFromStatus(finalStatus.status), 'completed', finalStatus.message);
          
          if (finalStatus.result) {
            console.log('📝 Setting result with narrative:', {
              narrativeLength: finalStatus.result.narrative.length,
              outputFile: finalStatus.result.output_file,
              processedFiles: finalStatus.result.processed_files
            });
            
            setResult({
              status: 'completed',
              message: 'Processing completed successfully!',
              narrativeScript: finalStatus.result.narrative,
              files: Array(finalStatus.result.processed_files).fill('processed_file.txt')
            });
            setEditableNarrative(finalStatus.result.narrative);
          } else {
            console.warn('⚠️ Completed job has no result data');
            // Even without result data, set a basic completed result
            setResult({
              status: 'completed',
              message: 'Processing completed, but no narrative data available.',
              narrativeScript: '',
              files: []
            });
          }
      
          // Mark files as processed
          setUploadedFiles(prev => prev.map(f => ({ ...f, status: 'processed' })));
          setProcessing(false);
        },
        (errorMessage: string) => {
          console.error('❌ Processing failed with error:', {
            jobId: uploadResponse.job_id,
            errorMessage,
            timestamp: new Date().toISOString()
          });

          // Processing failed
          setError(`Processing failed: ${errorMessage}`);
          setProcessing(false);
          setUploadedFiles(prev => prev.map(f => ({ ...f, status: 'error' })));
          
          // Update last step as error
          setProcessingSteps(prev => {
            const lastStep = prev[prev.length - 1];
            if (lastStep) {
              console.log('🔄 Updating last step with error:', {
                stepId: lastStep.id,
                oldStatus: lastStep.status,
                errorMessage
              });
              return prev.map(step => 
                step.id === lastStep.id 
                  ? { ...step, status: 'error', message: errorMessage }
                  : step
              );
            }
            console.warn('⚠️ No steps found to update with error');
            return prev;
          });
        }
      );

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Processing failed';
      console.error('❌ Video processing pipeline failed:', {
        error,
        errorMessage,
        uploadedFiles: uploadedFiles.length,
        timestamp: new Date().toISOString(),
        stack: error instanceof Error ? error.stack : undefined
      });

      setError(errorMessage);
      setProcessing(false);
      setUploadedFiles(prev => prev.map(f => ({ ...f, status: 'error' })));
    }
  };

  // Helper functions for mapping backend status to frontend steps
  const getStepIdFromStatus = (status: string): string => {
    switch (status) {
      case 'uploading':
        return 'upload';
      case 'processing':
        return 'video-processing';
      case 'generating_narrative':
        return 'nlp-processing';
      case 'completed':
        return 'nlp-processing';
      case 'error':
        return 'error';
      default:
        return 'processing';
    }
  };

  const getStepNameFromStatus = (status: string): string => {
    switch (status) {
      case 'uploading':
        return 'Upload';
      case 'processing':
        return 'Video Processing';
      case 'generating_narrative':
        return 'Narrative Generation';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Error';
      default:
        return 'Processing';
    }
  };

  // Submit edited narrative (placeholder for now)
  const submitEditedNarrative = async (narrative: string): Promise<{ success: boolean; message: string }> => {
    // TODO: This could be connected to a future API endpoint for further processing
    // For now, just simulate success
    await new Promise(resolve => setTimeout(resolve, 1000));
    return { success: true, message: 'Narrative script processed successfully! Ready for video generation.' };
  };

  const jumpToTimestamp = (timeString: string) => {
    if (!videoRef.current) return;
    
    // Parse timestamp format [HH:MM:SS]
    const match = timeString.match(/\[(\d{2}):(\d{2}):(\d{2})\]/);
    if (match) {
      const [, hours, minutes, seconds] = match;
      const timeInSeconds = parseInt(hours) * 3600 + parseInt(minutes) * 60 + parseInt(seconds);
      videoRef.current.currentTime = timeInSeconds;
    }
  };

  const handleSubmit = async () => {
    if (!editableNarrative.trim()) return;

    try {
      setProcessing(true);
      
      // Call submit API (placeholder)
      const response = await submitEditedNarrative(editableNarrative);
      
      if (response.success) {
        setSubmitSuccess(true);
        setIsEditing(false);
        
        // Show success for 3 seconds
        setTimeout(() => {
          setSubmitSuccess(false);
        }, 3000);
      } else {
        throw new Error(response.message);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Submission failed';
      setError(errorMessage);
    } finally {
      setProcessing(false);
    }
  };

  const clearAll = () => {
    uploadedFiles.forEach(f => URL.revokeObjectURL(f.videoUrl));
    setUploadedFiles([]);
    setCurrentVideoUrl('');
    setResult(null);
    setError(null);
    setEditableNarrative('');
    setIsEditing(false);
    setSubmitSuccess(false);
    setProcessingSteps([]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Scissors className="h-6 w-6 text-blue-400" />
          <h2 className="text-xl font-semibold text-gray-100">Video Processor</h2>
        </div>
        {uploadedFiles.length > 0 && (
          <button
            onClick={clearAll}
            className="px-3 py-1 text-sm text-gray-400 hover:text-red-400 transition-colors"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-blue-400 bg-blue-900/20'
            : 'border-gray-600 hover:border-gray-500 bg-gray-800/50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        {isDragActive ? (
          <p className="text-blue-400">Drop the video files here...</p>
        ) : (
          <>
            <p className="text-gray-300 mb-2">Drag & drop video files here, or click to select</p>
            <p className="text-gray-500 text-sm">Supports MP4, MOV, AVI, MKV, WebM, TS</p>
          </>
        )}
      </div>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-200 flex items-center gap-2">
            <FileVideo className="h-5 w-5" />
            Uploaded Files ({uploadedFiles.length})
          </h3>
          <div className="grid gap-3">
            {uploadedFiles.map((fileItem) => (
              <div 
                key={fileItem.id}
                className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                  fileItem.videoUrl === currentVideoUrl
                    ? 'border-blue-400 bg-blue-900/20'
                    : 'border-gray-600 bg-gray-800/50'
                }`}
              >
                <div 
                  className="flex items-center gap-3 flex-1 cursor-pointer"
                  onClick={() => selectVideo(fileItem.videoUrl)}
                >
                  <div className={`w-2 h-2 rounded-full ${
                    fileItem.status === 'uploaded' ? 'bg-gray-400' :
                    fileItem.status === 'processing' ? 'bg-yellow-400 animate-pulse' :
                    fileItem.status === 'processed' ? 'bg-green-400' :
                    'bg-red-400'
                  }`} />
                  <span className="text-gray-300 font-mono text-sm">{fileItem.file.name}</span>
                  <span className="text-gray-500 text-xs">
                    ({(fileItem.file.size / (1024 * 1024)).toFixed(1)} MB)
                  </span>
                  {fileItem.videoUrl === currentVideoUrl && (
                    <span className="text-blue-400 text-xs font-medium">• SELECTED</span>
                  )}
                </div>
                <button
                  onClick={() => removeFile(fileItem.id)}
                  className="text-gray-400 hover:text-red-400 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
          
          {/* Process Button */}
          <button
            onClick={processVideosWithAPI}
            disabled={processing || uploadedFiles.some(f => f.status === 'processing')}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-3 px-4 rounded-lg font-medium transition-colors"
          >
            {processing ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Play className="h-5 w-5" />
                Process Videos ({uploadedFiles.length})
              </>
            )}
          </button>
        </div>
      )}

      {/* Video Player */}
      {currentVideoUrl && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-200 flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Video Preview
          </h3>
          <video
            ref={videoRef}
            src={currentVideoUrl}
            controls
            className="w-full rounded-lg bg-black"
            style={{ maxHeight: '400px' }}
          />
        </div>
      )}

      {/* Processing Steps */}
      {processingSteps.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-200 flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Processing Status
          </h3>
          <div className="space-y-3">
            {processingSteps.map((step) => (
              <div key={step.id} className="border border-gray-600 rounded-lg p-4 bg-gray-800/50">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {step.status === 'processing' ? (
                      <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                    ) : step.status === 'completed' ? (
                      <CheckCircle className="h-4 w-4 text-green-400" />
                    ) : step.status === 'error' ? (
                      <AlertCircle className="h-4 w-4 text-red-400" />
                    ) : (
                      <Clock className="h-4 w-4 text-gray-400" />
                    )}
                    <span className="font-medium text-gray-200">{step.name}</span>
                  </div>
                  <span className="text-xs text-gray-500">{step.timestamp}</span>
                </div>
                <p className="text-sm text-gray-400 mb-2">{step.message}</p>
                {step.status === 'processing' && (
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${step.progress}%` }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="border border-red-500 rounded-lg p-4 bg-red-900/20">
          <div className="flex items-center gap-2 text-red-400 mb-2">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">Processing Error</span>
          </div>
          <div className="text-red-300 mb-2">{error}</div>
          
          {/* Additional error context for debugging */}
          <details className="mt-3">
            <summary className="text-sm text-red-400 cursor-pointer hover:text-red-300">
              🔍 Debug Information (Click to expand)
            </summary>
            <div className="mt-2 p-3 bg-red-950/30 rounded text-xs font-mono text-red-200 space-y-2">
              <div><strong>Timestamp:</strong> {new Date().toISOString()}</div>
              <div><strong>Job ID:</strong> {currentJobId || 'N/A'}</div>
              <div><strong>Files:</strong> {uploadedFiles.length} files uploaded</div>
              <div><strong>File Names:</strong> {uploadedFiles.map(f => f.file.name).join(', ')}</div>
              <div><strong>Processing Steps:</strong> {processingSteps.length} steps completed</div>
              <div className="pt-2">
                <strong>Recent Steps:</strong>
                <ul className="ml-4 mt-1">
                  {processingSteps.slice(-3).map(step => (
                    <li key={step.id}>
                      • {step.name}: {step.message} ({step.status})
                    </li>
                  ))}
                </ul>
              </div>
              <div className="pt-2 text-yellow-300">
                <strong>💡 Troubleshooting:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Check browser console for detailed API logs</li>
                  <li>• Verify backend server is running on localhost:8000</li>
                  <li>• Check backend console for "read of closed file" errors</li>
                  <li>• Ensure video files are not corrupted or too large</li>
                </ul>
              </div>
            </div>
          </details>
        </div>
      )}

      {/* Success Display */}
      {submitSuccess && (
        <div className="border border-green-500 rounded-lg p-4 bg-green-900/20">
          <div className="flex items-center gap-2 text-green-400">
            <CheckCircle className="h-5 w-5" />
            <span className="font-medium">Success</span>
          </div>
          <p className="text-green-300 mt-1">Narrative script submitted successfully!</p>
        </div>
      )}

      {/* Processing Result - Narrative Script */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-200 flex items-center gap-2">
              <Edit3 className="h-5 w-5" />
              Generated Narrative Script
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  isEditing 
                    ? 'bg-green-600 hover:bg-green-700 text-white' 
                    : 'bg-gray-600 hover:bg-gray-700 text-gray-200'
                }`}
              >
                {isEditing ? 'Preview' : 'Edit'}
              </button>
            </div>
          </div>

          <div className="border border-gray-600 rounded-lg bg-gray-800/50">
            {isEditing ? (
              <div className="p-4">
                <textarea
                  value={editableNarrative}
                  onChange={(e) => setEditableNarrative(e.target.value)}
                  className="w-full h-96 bg-gray-900 border border-gray-600 rounded-lg p-4 text-gray-200 font-mono text-sm resize-none focus:outline-none focus:border-blue-400"
                  placeholder="Edit your narrative script here..."
                  style={{ lineHeight: '1.6' }}
                />
                <div className="flex justify-end gap-3 mt-4">
                  <button
                    onClick={() => {
                      setEditableNarrative(result.narrativeScript);
                      setIsEditing(false);
                    }}
                    className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={processing || !editableNarrative.trim()}
                    className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    {processing ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4" />
                        Submit Script
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-4">
                <div className="prose prose-invert prose-sm max-w-none">
                  {editableNarrative.split('\n').map((line, index) => {
                    // Check if line starts with timestamp
                    const timestampMatch = line.match(/^\[(\d{2}:\d{2}:\d{2})\]/);
                    if (timestampMatch) {
                      const timestamp = timestampMatch[1];
                      const content = line.replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
                      return (
                        <div key={index} className="mb-4">
                          <button
                            onClick={() => jumpToTimestamp(line)}
                            className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 font-mono text-sm mb-2 transition-colors"
                          >
                            <Clock className="h-3 w-3" />
                            [{timestamp}]
                          </button>
                          <p className="text-gray-300 leading-relaxed">{content}</p>
                        </div>
                      );
                    } else if (line.trim()) {
                      return (
                        <p key={index} className="text-gray-300 leading-relaxed mb-4">
                          {line}
                        </p>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            )}
          </div>

          {!isEditing && (
            <div className="text-center">
              <button
                onClick={() => setIsEditing(true)}
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                <Edit3 className="h-4 w-4" />
                Edit Narrative Script
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CurrentItem; 
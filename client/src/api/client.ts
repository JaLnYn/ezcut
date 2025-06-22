import axios from 'axios';

// API base URL - can be configured via environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 1800000, // 30 minutes timeout for video uploads (vs 5 minutes before)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Enhanced logging utility
const logApiCall = (type: 'request' | 'response' | 'error', data: any) => {
  const timestamp = new Date().toISOString();
  const emoji = type === 'request' ? '🚀' : type === 'response' ? '✅' : '❌';
  
  console.group(`${emoji} API ${type.toUpperCase()} [${timestamp}]`);
  
  if (type === 'request') {
    console.log('Method:', data.method?.toUpperCase());
    console.log('URL:', data.url);
    console.log('Headers:', data.headers);
    if (data.data && !(data.data instanceof FormData)) {
      console.log('Data:', data.data);
    } else if (data.data instanceof FormData) {
      console.log('FormData with files:', Array.from(data.data.keys()));
    }
  } else if (type === 'response') {
    console.log('Status:', data.status, data.statusText);
    console.log('URL:', data.config.url);
    console.log('Response Data:', data.data);
    console.log('Response Headers:', data.headers);
  } else if (type === 'error') {
    console.error('Error Details:', {
      message: data.message,
      code: data.code,
      status: data.response?.status,
      statusText: data.response?.statusText,
      url: data.config?.url,
      method: data.config?.method,
      responseData: data.response?.data,
      stack: data.stack
    });
  }
  
  console.groupEnd();
};

// Add request interceptor for debugging
apiClient.interceptors.request.use(
  (config) => {
    logApiCall('request', config);
    return config;
  },
  (error) => {
    console.error('❌ API Request Setup Error:', error);
    logApiCall('error', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
apiClient.interceptors.response.use(
  (response) => {
    logApiCall('response', response);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.status, error.message);
    logApiCall('error', error);
    
    // Enhanced error context
    if (error.response?.status === 0 || error.code === 'ERR_NETWORK') {
      console.error('🚨 Backend server connection failed. Please check if the API server is running on', API_BASE_URL);
    } else if (error.response?.status >= 500) {
      console.error('🚨 Backend server error. Check backend logs for details.');
    } else if (error.response?.status >= 400) {
      console.error('🚨 Client request error:', error.response?.data);
    }
    
    return Promise.reject(error);
  }
);

// Types for API responses
export interface JobStatus {
  job_id: string;
  status: 'uploading' | 'processing' | 'generating_narrative' | 'completed' | 'error';
  progress: number;
  message: string;
  result?: {
    narrative: string;
    output_file: string;
    processed_files: number;
  };
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface UploadResponse {
  job_id: string;
  message: string;
  status_endpoint: string;
}

export interface JobsListResponse {
  jobs: Array<{
    job_id: string;
    status: string;
    progress: number;
    created_at: string;
    completed_at?: string;
  }>;
}

// Enhanced error utility
const enhanceError = (error: any, context: string) => {
  const enhancedError = new Error(`${context}: ${error.message || 'Unknown error'}`);
  (enhancedError as any).originalError = error;
  (enhancedError as any).context = context;
  (enhancedError as any).timestamp = new Date().toISOString();
  
  if (error.response) {
    (enhancedError as any).status = error.response.status;
    (enhancedError as any).statusText = error.response.statusText;
    (enhancedError as any).responseData = error.response.data;
  }
  
  console.error('Enhanced Error Details:', {
    context,
    message: error.message,
    status: error.response?.status,
    responseData: error.response?.data,
    originalError: error
  });
  
  return enhancedError;
};

// API functions with enhanced error handling
export const api = {
  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      throw enhanceError(error, 'Health check failed');
    }
  },

  // Upload videos and start processing
  async uploadVideos(files: File[]): Promise<UploadResponse> {
    try {
      console.log(`📤 Starting upload of ${files.length} files:`, files.map(f => ({
        name: f.name,
        size: f.size,
        type: f.type
      })));
      
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
        console.log(`📁 Added file to FormData: ${file.name} (${file.size} bytes)`);
      });

      const response = await apiClient.post('/upload-videos', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 1800000, // 30 minutes timeout specifically for upload
      });
      
      console.log('📤 Upload successful, job ID:', response.data.job_id);
      return response.data;
    } catch (error) {
      throw enhanceError(error, `Failed to upload ${files.length} video files`);
    }
  },

  // Get job status
  async getJobStatus(jobId: string): Promise<JobStatus> {
    try {
      const response = await apiClient.get(`/job/${jobId}`, {
        timeout: 10000, // 10 second timeout for status checks (quick)
      });
      console.log(`📊 Job ${jobId} status:`, {
        status: response.data.status,
        progress: response.data.progress,
        message: response.data.message,
        error: response.data.error
      });
      return response.data;
    } catch (error) {
      throw enhanceError(error, `Failed to get status for job ${jobId}`);
    }
  },

  // List all jobs
  async listJobs(): Promise<JobsListResponse> {
    try {
      const response = await apiClient.get('/jobs');
      console.log(`📋 Retrieved ${response.data.jobs.length} jobs from history`);
      return response.data;
    } catch (error) {
      throw enhanceError(error, 'Failed to list jobs');
    }
  },

  // Delete a job
  async deleteJob(jobId: string): Promise<{ message: string }> {
    try {
      const response = await apiClient.delete(`/job/${jobId}`);
      console.log(`🗑️ Deleted job ${jobId}:`, response.data.message);
      return response.data;
    } catch (error) {
      throw enhanceError(error, `Failed to delete job ${jobId}`);
    }
  },

  // Clear all jobs
  async clearAllJobs(): Promise<{ message: string }> {
    try {
      const response = await apiClient.delete('/jobs');
      console.log('🧹 Cleared all jobs:', response.data.message);
      return response.data;
    } catch (error) {
      throw enhanceError(error, 'Failed to clear all jobs');
    }
  },
};

// Enhanced polling helper for job status
export const pollJobStatus = async (
  jobId: string,
  onUpdate: (status: JobStatus) => void,
  onComplete: (result: JobStatus) => void,
  onError: (error: string) => void,
  intervalMs = 2000
): Promise<void> => {
  console.log(`🔄 Starting to poll job ${jobId} every ${intervalMs}ms`);
  let pollCount = 0;
  
  const poll = async () => {
    pollCount++;
    try {
      console.log(`🔄 Poll attempt #${pollCount} for job ${jobId}`);
      const status = await api.getJobStatus(jobId);
      
      console.log(`🔄 Poll update #${pollCount} for job ${jobId}:`, {
        status: status.status,
        progress: status.progress,
        message: status.message,
        hasError: !!status.error,
        hasResult: !!status.result,
        resultKeys: status.result ? Object.keys(status.result) : null
      });
      
      // Always call onUpdate to keep UI in sync
      onUpdate(status);

      if (status.status === 'completed') {
        console.log(`✅ Job ${jobId} completed successfully after ${pollCount} polls`);
        console.log(`✅ Final status details:`, {
          status: status.status,
          progress: status.progress,
          message: status.message,
          result: status.result,
          resultNarrativeLength: status.result?.narrative?.length || 0
        });
        onComplete(status);
        return; // Stop polling
      } else if (status.status === 'error') {
        const errorMsg = status.error || 'Processing failed';
        console.error(`❌ Job ${jobId} failed after ${pollCount} polls:`, errorMsg);
        onError(errorMsg);
        return; // Stop polling
      } else {
        // Continue polling
        console.log(`⏳ Job ${jobId} still processing (${status.status}), will poll again in ${intervalMs}ms (poll #${pollCount})`);
        setTimeout(poll, intervalMs);
      }
    } catch (error: any) {
      const errorMsg = error.message || 'Failed to get job status';
      console.error(`❌ Polling error for job ${jobId} on poll #${pollCount}:`, {
        error: error,
        message: errorMsg,
        status: error.response?.status,
        statusText: error.response?.statusText
      });
      onError(errorMsg);
    }
  };

  await poll();
};

export default api; 
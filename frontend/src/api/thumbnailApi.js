const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const createJob = async (formData) => {
  const response = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || 'Failed to create job');
  }
  return response.json();
};

export const subscribeToJob = (jobId, callbacks) => {
  const eventSource = new EventSource(`${API_BASE_URL}/api/jobs/${jobId}/stream`);

  eventSource.addEventListener('job_started', (e) => {
    const data = JSON.parse(e.data);
    callbacks.onStarted && callbacks.onStarted(data);
  });

  eventSource.addEventListener('step_progress', (e) => {
    const data = JSON.parse(e.data);
    callbacks.onProgress && callbacks.onProgress(data);
  });

  eventSource.addEventListener('job_completed', (e) => {
    const data = JSON.parse(e.data);
    callbacks.onCompleted && callbacks.onCompleted(data);
    eventSource.close();
  });

  eventSource.addEventListener('job_failed', (e) => {
    const data = JSON.parse(e.data);
    callbacks.onFailed && callbacks.onFailed(data);
    eventSource.close();
  });

  eventSource.onerror = (err) => {
    console.error('SSE Error:', err);
    eventSource.close();
    callbacks.onError && callbacks.onError(err);
  };

  return () => {
    eventSource.close();
  };
};

export const getAllJobs = async () => {
  const response = await fetch(`${API_BASE_URL}/api/jobs`);
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || 'Failed to fetch jobs history');
  }
  return response.json();
};

export const clearAllJobs = async () => {
  const response = await fetch(`${API_BASE_URL}/api/jobs`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to clear history');
  return response.json();
};

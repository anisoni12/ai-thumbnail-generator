import React, { useState, useEffect } from 'react';
import UploadForm from './forms/UploadForm';
import LoadingState from './LoadingState';
import ResultsGallery from './ResultsGallery';
import HeroSection from './HeroSection';
import { createJob, subscribeToJob } from '../api/thumbnailApi';

export default function GeneratePanel() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progressStep, setProgressStep] = useState('');
  const [results, setResults] = useState([]);
  const [errorMsg, setErrorMsg] = useState('');

  const handleGenerate = async (formData) => {
    try {
      setIsGenerating(true);
      setProgressStep('Submitting job...');
      setErrorMsg('');
      const data = await createJob(formData);
      setJobId(data.job_id);
    } catch (err) {
      console.error(err);
      setIsGenerating(false);
      setErrorMsg(err.message || 'Failed to submit job.');
    }
  };

  useEffect(() => {
    if (!jobId) return;

    const cleanup = subscribeToJob(jobId, {
      onStarted: () => { setProgressStep('Job started...'); },
      onProgress: (data) => { setProgressStep(data.step); },
      onCompleted: (data) => {
        setIsGenerating(false);
        setResults(data.thumbnails);
        setShowResults(true);
        setJobId(null);
      },
      onFailed: (data) => {
        setIsGenerating(false);
        setErrorMsg(data.error || 'The job failed.');
        setJobId(null);
      },
      onError: () => console.warn('SSE disconnected')
    });

    return cleanup;
  }, [jobId]);

  if (showResults) {
    return <ResultsGallery thumbnails={results} onGenerateMore={() => setShowResults(false)} />;
  }

  return (
    <div className="w-full max-w-xl">
      <HeroSection
        title={<><span className="text-primary drop-shadow-[0_0_10px_rgba(0,242,255,0.4)]">Thumbnail</span>.PRO</>}
        subtitle="Upload your headshot, describe your video, get thumbnails in seconds."
      />
      {errorMsg && (
        <div className="mb-4 p-4 bg-red-900/30 border border-red-500/50 rounded-xl text-red-200 font-label-sm text-sm">
          <strong>Error:</strong> {errorMsg}
        </div>
      )}
      <div className="glass-card rounded-[2.5rem] p-8 md:p-12 relative overflow-hidden">
        {isGenerating ? (
          <LoadingState stepMessage={progressStep} />
        ) : (
          <UploadForm onSubmit={handleGenerate} />
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import ThumbnailCard from '../components/cards/ThumbnailCard';
import HeroSection from '../components/HeroSection';
import { getAllJobs } from '../api/thumbnailApi';

export default function History() {
  const [historyItems, setHistoryItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await getAllJobs();
        // Flatten all thumbnails from completed jobs
        const allThumbnails = data
          .filter(job => job.status === 'completed')
          .flatMap(job => job.thumbnails);
        setHistoryItems(allThumbnails);
      } catch (err) {
        console.error("Failed to fetch history:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  return (
    <div className="w-full max-w-5xl mx-auto pb-20">
      <HeroSection 
        title="Your History" 
        subtitle="Past generated thumbnails and assets." 
      />
      {loading ? (
        <div className="flex justify-center mt-20">
          <div className="w-16 h-16 rounded-full border-4 border-white/10 border-t-primary animate-spin glow-primary"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-12">
          {historyItems.map(thumb => (
            <ThumbnailCard key={thumb.id} thumbnail={thumb} />
          ))}
          {historyItems.length === 0 && (
            <div className="col-span-full text-center text-on-surface-variant font-body-lg mt-10">
              No generated thumbnails found yet. Go to the Studio to create some!
            </div>
          )}
        </div>
      )}
    </div>
  );
}

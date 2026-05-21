import React, { useState, useEffect } from 'react';
import ThumbnailCard from '../components/cards/ThumbnailCard';
import HeroSection from '../components/HeroSection';
import { getAllJobs, clearAllJobs } from '../api/thumbnailApi';

export default function History() {
  const [historyItems, setHistoryItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await getAllJobs();
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

  const handleClear = async () => {
    if (!window.confirm('Delete all history? This cannot be undone.')) return;
    setClearing(true);
    try {
      await clearAllJobs();
      setHistoryItems([]);
    } catch (err) {
      console.error('Failed to clear history:', err);
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto pb-20">
      <div className="flex items-center justify-between">
        <HeroSection
          title="Your History"
          subtitle="Past generated thumbnails and assets."
        />
        {historyItems.length > 0 && (
          <button
            onClick={handleClear}
            disabled={clearing}
            className="shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl border border-red-500/30 text-red-400 hover:bg-red-500/10 text-xs font-bold uppercase tracking-widest transition-all disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-sm">delete_sweep</span>
            {clearing ? 'Clearing...' : 'Clear All'}
          </button>
        )}
      </div>
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

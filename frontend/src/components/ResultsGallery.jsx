import React from 'react';
import ThumbnailCard from './cards/ThumbnailCard';
import HeroSection from './HeroSection';

export default function ResultsGallery({ thumbnails, onGenerateMore }) {
  const displayThumbnails = thumbnails || [];

  return (
    <div className="w-full">
      <HeroSection
        title={<span className="text-primary drop-shadow-[0_0_10px_rgba(0,242,255,0.4)]">Your Thumbnails</span>}
        subtitle="Download your favorite or generate fresh variations."
      />

      {displayThumbnails.length === 0 ? (
        <div className="text-center text-on-surface-variant mt-12">
          No thumbnails generated yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10 mt-12">
          {displayThumbnails.map(thumb => (
            <ThumbnailCard key={thumb.id} thumbnail={thumb} />
          ))}
        </div>
      )}

      <div className="mt-16 flex justify-center pb-24">
        <button
          onClick={onGenerateMore}
          className="bg-primary-container text-on-primary-container px-10 py-4 rounded-2xl font-label-sm text-[14px] font-extrabold primary-glow hover:scale-105 transition-all flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-lg">refresh</span>
          GENERATE MORE VARIATIONS
        </button>
      </div>
    </div>
  );
}

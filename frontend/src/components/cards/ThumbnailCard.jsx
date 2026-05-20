import React from 'react';

export default function ThumbnailCard({ thumbnail }) {
  const src = thumbnail.image_url || thumbnail.image;
  return (
    <div className="group relative flex flex-col glass-card rounded-2xl overflow-hidden transition-all duration-500 hover:translate-y-[-4px] glow-border">
      <div className="aspect-video relative overflow-hidden bg-surface-container-lowest">
        <img
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
          src={src}
          alt={thumbnail.title || 'Generated thumbnail'}
          loading="lazy"
        />
        <span className="absolute top-3 left-3 px-2 py-1 rounded-md text-[10px] font-bold tracking-widest uppercase bg-black/60 text-primary border border-primary/30">HD • 1280×720</span>
      </div>
      <div className="p-5 space-y-3">
        {thumbnail.title && (
          <p className="text-on-surface text-sm font-semibold truncate" title={thumbnail.title}>{thumbnail.title}</p>
        )}
        <a
          href={src}
          download
          target="_blank"
          rel="noreferrer"
          className="w-full py-3 bg-primary-container/10 hover:bg-primary-container text-primary hover:text-on-primary-container border border-primary/20 rounded-xl font-label-sm text-[12px] font-bold transition-all flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-lg">download</span>
          DOWNLOAD THUMBNAIL
        </a>
      </div>
    </div>
  );
}

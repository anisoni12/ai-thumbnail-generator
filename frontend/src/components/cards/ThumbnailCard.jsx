import React, { useState, useEffect } from 'react';

export default function ThumbnailCard({ thumbnail }) {
  const src = thumbnail.image_url || thumbnail.image;
  const [downloading, setDownloading] = useState(false);
  const [preview, setPreview] = useState(false);

  useEffect(() => {
    if (!preview) return;
    const onKey = (e) => { if (e.key === 'Escape') setPreview(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [preview]);

  const handleDownload = async () => {
    if (downloading) return;
    setDownloading(true);
    try {
      const res = await fetch(src);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `thumbnail_${thumbnail.title?.replace(/\s+/g, '_') || 'download'}.jpg`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      window.open(src, '_blank');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <>
      {/* Lightbox */}
      {preview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4"
          onClick={() => setPreview(false)}
        >
          <div className="relative max-w-5xl w-full" onClick={(e) => e.stopPropagation()}>
            <img
              src={src}
              alt={thumbnail.title || 'Thumbnail preview'}
              className="w-full rounded-xl shadow-2xl"
            />
            <div className="absolute top-3 right-3 flex gap-2">
              <button
                onClick={handleDownload}
                className="flex items-center gap-1 px-3 py-2 rounded-lg bg-black/70 text-white text-xs font-bold hover:bg-primary transition-all"
              >
                <span className="material-symbols-outlined text-sm">download</span>
                DOWNLOAD
              </button>
              <button
                onClick={() => setPreview(false)}
                className="flex items-center justify-center w-9 h-9 rounded-lg bg-black/70 text-white hover:bg-red-500 transition-all"
              >
                <span className="material-symbols-outlined text-sm">close</span>
              </button>
            </div>
            {thumbnail.title && (
              <p className="text-center text-white/70 text-sm mt-3 font-semibold">{thumbnail.title}</p>
            )}
          </div>
        </div>
      )}

      {/* Card */}
      <div className="group relative flex flex-col glass-card rounded-2xl overflow-hidden transition-all duration-500 hover:translate-y-[-4px] glow-border">
        <div
          className="aspect-video relative overflow-hidden bg-surface-container-lowest cursor-zoom-in"
          onClick={() => setPreview(true)}
        >
          <img
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
            src={src}
            alt={thumbnail.title || 'Generated thumbnail'}
            loading="lazy"
          />
          <span className="absolute top-3 left-3 px-2 py-1 rounded-md text-[10px] font-bold tracking-widest uppercase bg-black/60 text-primary border border-primary/30">HD • 1280×720</span>
          <span className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/30">
            <span className="material-symbols-outlined text-white text-4xl drop-shadow-lg">zoom_in</span>
          </span>
        </div>
        <div className="p-5 space-y-3">
          {thumbnail.title && (
            <p className="text-on-surface text-sm font-semibold truncate" title={thumbnail.title}>{thumbnail.title}</p>
          )}
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="w-full py-3 bg-primary-container/10 hover:bg-primary-container text-primary hover:text-on-primary-container border border-primary/20 rounded-xl font-label-sm text-[12px] font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-outlined text-lg">
              {downloading ? 'hourglass_empty' : 'download'}
            </span>
            {downloading ? 'DOWNLOADING...' : 'DOWNLOAD THUMBNAIL'}
          </button>
        </div>
      </div>
    </>
  );
}

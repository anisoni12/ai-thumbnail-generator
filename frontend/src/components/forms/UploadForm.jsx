import React, { useState, useRef, useEffect } from 'react';

const MAX_SIZE_MB = 8;

export default function UploadForm({ onSubmit }) {
  const [prompt, setPrompt] = useState('');
  const [styleCount, setStyleCount] = useState(2);
  const [headshot, setHeadshot] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [localError, setLocalError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!headshot) { setPreviewUrl(null); return; }
    const url = URL.createObjectURL(headshot);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [headshot]);

  const acceptFile = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setLocalError('Please select a valid image file.');
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setLocalError(`Image must be smaller than ${MAX_SIZE_MB}MB.`);
      return;
    }
    setLocalError('');
    setHeadshot(file);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!headshot) { setLocalError('Please upload a headshot photo.'); return; }
    if (!prompt.trim()) { setLocalError('Please describe your video idea.'); return; }
    setLocalError('');
    const formData = new FormData();
    formData.append('prompt', prompt.trim());
    formData.append('style_count', styleCount);
    formData.append('headshot', headshot);
    onSubmit(formData);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) acceptFile(e.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) acceptFile(e.dataTransfer.files[0]);
  };

  return (
    <form className="space-y-8" onSubmit={handleSubmit}>
      {/* Headshot Upload */}
      <div className="space-y-3">
        <label className="font-label-sm text-[11px] uppercase tracking-[0.2em] text-primary/60 ml-1 font-semibold">Headshot Photo</label>
        <div
          onClick={() => fileInputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          className={`neon-border rounded-2xl min-h-44 flex flex-col items-center justify-center gap-4 transition-all cursor-pointer group p-4 ${dragActive ? 'bg-primary/10 scale-[1.01]' : 'bg-surface-container-lowest/30 hover:bg-primary/5'}`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />
          {previewUrl ? (
            <div className="flex items-center gap-4 w-full">
              <img src={previewUrl} alt="preview" className="w-20 h-20 rounded-xl object-cover border border-primary/40" />
              <div className="flex-1 text-left">
                <p className="font-label-sm text-on-surface font-semibold truncate max-w-[260px]">{headshot.name}</p>
                <p className="text-[10px] text-on-surface-variant mt-1">{(headshot.size / 1024).toFixed(0)} KB • click to change</p>
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setHeadshot(null); }}
                className="text-on-surface-variant hover:text-primary transition"
                aria-label="Remove image"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
          ) : (
            <>
              <span className="material-symbols-outlined text-primary text-3xl group-hover:scale-110 transition-transform">add_a_photo</span>
              <div className="text-center">
                <p className="font-label-sm text-on-surface opacity-80 font-semibold">Drag headshot or click to upload</p>
                <p className="text-[10px] text-on-surface-variant mt-1">PNG, JPG • max {MAX_SIZE_MB}MB</p>
              </div>
            </>
          )}
        </div>
        {localError && (
          <p className="text-red-400 text-xs font-label-sm pl-1">{localError}</p>
        )}
      </div>

      {/* Description */}
      <div className="space-y-3">
        <label className="font-label-sm text-[11px] uppercase tracking-[0.2em] text-primary/60 ml-1 font-semibold">Describe your video</label>
        <textarea
          className="w-full bg-surface-container-highest/20 border border-white/5 p-5 rounded-xl text-on-surface font-body-md placeholder:text-on-surface-variant/40 transition-all h-28 resize-none focus:bg-surface-container-highest/40 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
          placeholder="e.g. React JS full course in 5 hours, beginner to advanced"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        ></textarea>
        <div className="flex flex-wrap gap-2 pt-1">
          {[
            'React JS full course in 5 hours',
            'System Design crash course',
          ].map(s => (
            <button
              key={s}
              type="button"
              onClick={() => setPrompt(s)}
              className="text-[11px] px-3 py-1.5 rounded-full border border-white/10 hover:border-primary/50 hover:text-primary text-on-surface-variant transition"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Number of Styles */}
      <div className="space-y-3">
        <label className="font-label-sm text-[11px] uppercase tracking-[0.2em] text-primary/60 ml-1 font-semibold">Number of styles</label>
        <div className="grid grid-cols-3 gap-3">
          {[1, 2, 3].map(num => (
            <button
              key={num}
              type="button"
              onClick={() => setStyleCount(num)}
              className={`py-3 rounded-xl transition-all active:scale-95 ${styleCount === num
                  ? 'border border-primary text-primary bg-primary/5 neon-border'
                  : 'border border-white/10 hover:border-primary/50 text-on-surface bg-surface-container-lowest/30'
                }`}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      {/* Generate Button */}
      <div className="pt-4">
        <button type="submit" className="w-full py-5 rounded-2xl bg-primary-container text-on-primary-container font-display-lg text-[18px] font-extrabold uppercase tracking-widest glow-primary transition-all hover:brightness-110 active:scale-95 flex items-center justify-center gap-3">
          <span>Generate Thumbnails</span>
          <span className="material-symbols-outlined text-2xl">bolt</span>
        </button>
      </div>
    </form>
  );
}

import React from 'react';

export default function LoadingState({ stepMessage }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 space-y-6">
      <div className="relative">
        <div className="w-20 h-20 rounded-full border-4 border-white/10 border-t-primary animate-spin glow-primary"></div>
        <span className="material-symbols-outlined absolute inset-0 m-auto text-primary text-2xl flex items-center justify-center" style={{display:'flex',alignItems:'center',justifyContent:'center'}}>auto_awesome</span>
      </div>
      <div className="text-center space-y-2 max-w-sm">
        <h3 className="font-display-lg text-[22px] font-extrabold text-white tracking-tight">Cooking your thumbnails…</h3>
        <p className="text-on-surface-variant font-body-md opacity-80 text-sm min-h-[1.5em]">{stepMessage || 'Initializing pipeline…'}</p>
        <p className="text-on-surface-variant/50 text-[11px] uppercase tracking-[0.2em] mt-3">This usually takes 10–20 seconds</p>
      </div>
    </div>
  );
}

import React from 'react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <header className="absolute top-0 left-0 w-full z-50 flex justify-between items-center px-10 py-6 bg-transparent">
      <div className="font-display-lg text-[24px] font-extrabold tracking-tighter text-primary drop-shadow-[0_0_8px_rgba(0,242,255,0.6)] md:hidden">
        THUMBNAIL.PRO
      </div>
      <div className="hidden md:block"></div> {/* Spacer for desktop where logo is in sidebar */}

      <div className="flex items-center gap-6">
        <div className="hidden md:flex gap-6 text-on-surface-variant">
          <Link to="/" className="hover:text-primary transition-colors text-label-sm uppercase tracking-widest font-semibold">Studio</Link>
          <Link to="/history" className="hover:text-primary transition-colors text-label-sm uppercase tracking-widest font-semibold">History</Link>
        </div>
        <a
          href="https://github.com/anisoni12"
          target="_blank"
          rel="noreferrer"
          className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 hover:border-primary/40 text-on-surface-variant hover:text-primary transition text-xs uppercase tracking-widest font-semibold"
        >
          <span className="material-symbols-outlined text-base">code</span>
          GitHub
        </a>
      </div>
    </header>
  );
}

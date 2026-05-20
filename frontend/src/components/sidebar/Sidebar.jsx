import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  return (
    <aside className="w-64 bg-surface-container-lowest border-r border-white/5 flex-col hidden md:flex z-50">
      <div className="p-6">
        <Link to="/" className="font-display-lg text-[20px] font-extrabold tracking-tighter text-primary drop-shadow-[0_0_8px_rgba(0,242,255,0.6)]">
          THUMBNAIL.PRO
        </Link>
      </div>
      <nav className="flex-1 px-4 py-6 space-y-2">
        <Link to="/" className={`block px-4 py-3 rounded-xl font-label-sm uppercase tracking-widest transition-all ${isActive('/') ? 'bg-primary/10 text-primary neon-border' : 'text-on-surface-variant hover:text-on-surface hover:bg-white/5'}`}>
          Studio
        </Link>
        <Link to="/history" className={`block px-4 py-3 rounded-xl font-label-sm uppercase tracking-widest transition-all ${isActive('/history') ? 'bg-primary/10 text-primary neon-border' : 'text-on-surface-variant hover:text-on-surface hover:bg-white/5'}`}>
          History
        </Link>
      </nav>
      <div className="p-6 border-t border-white/5">
        <div className="text-[10px] text-on-surface-variant/30 font-label-sm tracking-tighter">
          © 2026 THUMBNAIL.PRO
        </div>
      </div>
    </aside>
  );
}

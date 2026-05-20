import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/navbar/Navbar';
import Sidebar from '../components/sidebar/Sidebar';

export default function MainLayout() {
  return (
    <div className="flex h-screen bg-obsidian text-on-surface font-body-md">
      {/* Sidebar hidden on mobile, visible on medium screens */}
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden relative">
        <Navbar />
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 pt-24 relative">
          {/* Ambient Glow Effects in Background */}
          <div className="fixed -top-32 -right-32 w-80 h-80 bg-primary/5 blur-[120px] rounded-full pointer-events-none"></div>
          <div className="fixed -bottom-32 -left-32 w-80 h-80 bg-primary/5 blur-[120px] rounded-full pointer-events-none"></div>
          
          <div className="relative z-10 w-full h-full max-w-6xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

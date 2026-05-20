import React from 'react';

export default function HeroSection({ title, subtitle }) {
  return (
    <div className="text-center space-y-3 mb-10">
      <h1 className="font-display-lg text-[32px] md:text-[48px] font-extrabold text-white tracking-tight">
        {title}
      </h1>
      <p className="text-on-surface-variant font-body-md opacity-70">
        {subtitle}
      </p>
    </div>
  );
}

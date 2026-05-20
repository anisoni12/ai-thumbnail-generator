import React from 'react';
import GeneratePanel from '../components/GeneratePanel';

export default function Generate() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-10rem)] w-full pb-24">
      <div className="w-full flex flex-col items-center">
        <GeneratePanel />
      </div>
    </div>
  );
}
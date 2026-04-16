import React from 'react';
import { Outlet } from 'react-router-dom';
import { Topbar } from './Topbar';
import { Rail } from './Rail';

export const Shell: React.FC = () => {
  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--bg0)]">
      <Topbar />
      <div className="flex flex-1 overflow-hidden">
        <Rail />
        <main className="flex-1 overflow-hidden relative">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

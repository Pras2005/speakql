import React from 'react';
import { Database, Search, ShieldCheck, Terminal, Settings } from 'lucide-react';
import { NavLink } from 'react-router-dom';

export const Rail: React.FC = () => {
  const iconSize = 16;
  const activeClass = "text-[var(--amber)] bg-[var(--bg3)]";
  const inactiveClass = "text-[var(--t3)] hover:text-[var(--t2)] hover:bg-[var(--bg2)]";

  return (
    <aside className="w-[var(--rail-w)] bg-[var(--bg1)] border-r border-[var(--bd)] flex flex-col items-center py-4 gap-4 shrink-0">
      <NavLink 
        to="/" 
        className={({ isActive }) => `p-1.5 transition-colors ${isActive ? activeClass : inactiveClass}`}
        title="Workbench"
      >
        <Terminal size={iconSize} />
      </NavLink>
      <NavLink 
        to="/catalog" 
        className={({ isActive }) => `p-1.5 transition-colors ${isActive ? activeClass : inactiveClass}`}
        title="Catalog"
      >
        <Search size={iconSize} />
      </NavLink>
      <NavLink 
        to="/audit" 
        className={({ isActive }) => `p-1.5 transition-colors ${isActive ? activeClass : inactiveClass}`}
        title="Audit"
      >
        <Database size={iconSize} />
      </NavLink>
      <NavLink 
        to="/policy" 
        className={({ isActive }) => `p-1.5 transition-colors ${isActive ? activeClass : inactiveClass}`}
        title="Policy"
      >
        <ShieldCheck size={iconSize} />
      </NavLink>
      <div className="mt-auto">
        <button className={`p-1.5 ${inactiveClass}`}>
          <Settings size={iconSize} />
        </button>
      </div>
    </aside>
  );
};

import React from 'react';
import { useThemeStore } from '../../store/themeStore';
import { Sun, Moon, LayoutGrid, ChevronRight } from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';

export const Topbar: React.FC = () => {
  const { theme, toggleTheme } = useThemeStore();
  const location = useLocation();

  const getBreadcrumb = () => {
    const path = location.pathname;
    if (path === '/') return 'WORKBENCH';
    return path.substring(1).toUpperCase();
  };

  const navItems = [
    { label: 'WORKBENCH', to: '/' },
    { label: 'AUDIT VAULT', to: '/audit' },
    { label: 'CATALOG', to: '/catalog' },
    { label: 'POLICY', to: '/policy' },
    { label: 'APPROVALS', to: '/approvals' },
  ];

  return (
    <header className="h-[var(--topbar-h)] bg-[var(--bg1)] border-b border-[var(--bd)] flex items-center justify-between px-3 shrink-0">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-1.5 select-none cursor-default">
          <LayoutGrid size={14} className="text-[var(--amber)]" />
          <span className="text-[13px] font-medium flex">
            <span className="text-[var(--t1)]">SPEAK</span>
            <span className="text-[var(--amber)]">QL</span>
          </span>
        </div>

        <div className="flex items-center gap-2 text-[10px] text-[var(--t3)] tracking-tight">
          <span>SPEAKEASY_ENT</span>
          <ChevronRight size={10} className="text-[var(--t4)]" />
          <span className="text-[var(--t2)]">{getBreadcrumb()}</span>
        </div>
      </div>

      <nav className="flex items-center h-full">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => 
              `h-full flex items-center px-4 text-[10px] font-medium tracking-[0.07em] border-b-2 transition-colors ${
                isActive 
                  ? 'text-[var(--amber)] border-[var(--amber)]' 
                  : 'text-[var(--t3)] border-transparent hover:text-[var(--t2)]'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="flex items-center gap-3">
        <button 
          onClick={toggleTheme}
          className="p-1.5 text-[var(--t3)] hover:text-[var(--t2)] transition-colors"
          title={theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
        </button>
        <div className="w-[24px] h-[24px] bg-[var(--bg3)] border border-[var(--bd2)] flex items-center justify-center text-[10px] text-[var(--t2)] font-medium">
          JD
        </div>
      </div>
    </header>
  );
};

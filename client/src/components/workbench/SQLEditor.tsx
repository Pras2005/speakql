import React from 'react';
import { PanelHeader } from '../shared/PanelHeader';
import { Tag } from '../shared/Tag';
import { Play, Copy, RotateCcw } from 'lucide-react';
import { useWorkbenchStore } from '../../store/workbenchStore';

export const SQLEditor: React.FC = () => {
  const { sql, setSql, setStatus } = useWorkbenchStore();

  const lines = sql.split('\n');

  const handleRun = () => {
    setStatus('executing');
    // Execution logic
  };

  const handleReset = () => {
    // Reset logic
  };

  const actions = (
    <>
      <button 
        onClick={handleReset}
        className="p-1 text-[var(--t3)] hover:text-[var(--t2)] transition-colors"
        title="Reset"
      >
        <RotateCcw size={14} />
      </button>
      <button 
        className="p-1 text-[var(--t3)] hover:text-[var(--t2)] transition-colors"
        title="Copy SQL"
      >
        <Copy size={14} />
      </button>
      <button 
        onClick={handleRun}
        className="flex items-center gap-1.5 px-2 py-1 bg-[var(--amber-bg)] border border-[var(--amber-bd)] text-[var(--amber-t)] text-[10px] font-medium uppercase tracking-wider hover:bg-[var(--amber-bd)] transition-colors"
      >
        <Play size={10} fill="currentColor" />
        <span>Execute</span>
      </button>
    </>
  );

  return (
    <div className="flex-1 flex flex-col min-w-0 border-r border-[var(--bd)] overflow-hidden">
      <PanelHeader 
        title="SQL Workbench" 
        tags={<Tag label="Draft" variant="amber" />}
        actions={actions}
      />
      <div className="flex-1 bg-[var(--bg2)] overflow-auto font-mono text-[11px] flex">
        {/* Line Numbers */}
        <div className="w-[32px] bg-[var(--bg1)] border-r border-[var(--bd)] py-3 flex flex-col items-center shrink-0">
          {lines.map((_, i) => (
            <div key={i} className="text-[var(--sql-linenum)] h-[16.5px] leading-[16.5px]">
              {i + 1}
            </div>
          ))}
        </div>
        
        {/* SQL Content */}
        <div className="flex-1 py-3 px-4 relative min-w-fit">
          <textarea
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            spellCheck={false}
            autoCapitalize="none"
            className="absolute inset-0 w-full h-full bg-transparent border-none outline-none resize-none py-3 px-4 text-[var(--t1)] leading-[16.5px] whitespace-pre overflow-hidden"
          />
          {/* Simple syntax highlighting overlay would go here for a production app */}
          <pre className="leading-[16.5px] pointer-events-none text-transparent">
            {sql}
          </pre>
        </div>
      </div>
    </div>
  );
};

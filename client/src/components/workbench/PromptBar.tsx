import React, { useState } from 'react';
import { useWorkbenchStore } from '../../store/workbenchStore';
import { Terminal, CornerDownLeft } from 'lucide-react';

export const PromptBar: React.FC = () => {
  const { prompt, setPrompt, setStatus } = useWorkbenchStore();
  const [localPrompt, setLocalPrompt] = useState(prompt);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!localPrompt.trim()) return;
    setPrompt(localPrompt);
    setStatus('generating');
    // Generation logic would go here
  };

  return (
    <div className="h-[var(--prompt-h)] bg-[var(--bg1)] border-t border-[var(--bd)] flex items-center px-4 shrink-0">
      <div className="flex items-center gap-3 w-full">
        <Terminal size={14} className="text-[var(--t3)]" />
        <form onSubmit={handleSubmit} className="flex-1 flex items-center relative">
          <input
            type="text"
            value={localPrompt}
            onChange={(e) => setLocalPrompt(e.target.value)}
            placeholder="Ask anything about the data... (e.g. 'Show me top 10 users by AUM')"
            className="w-full bg-transparent border-none outline-none text-[11px] font-mono text-[var(--t1)] placeholder:text-[var(--t4)] placeholder:font-sans"
          />
          {localPrompt && (
            <button 
              type="submit"
              className="absolute right-0 flex items-center gap-1.5 text-[9px] font-medium text-[var(--t3)] uppercase tracking-wider"
            >
              <span>Generate</span>
              <CornerDownLeft size={10} />
            </button>
          )}
          {!localPrompt && (
             <div className="absolute right-0 flex items-center gap-1.5 text-[9px] font-medium text-[var(--t4)] uppercase tracking-wider select-none">
              <span>ENTER TO RUN</span>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

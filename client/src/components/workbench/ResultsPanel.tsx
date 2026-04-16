import React from 'react';
import { PanelHeader } from '../shared/PanelHeader';
import { Tag } from '../shared/Tag';
import { useWorkbenchStore } from '../../store/workbenchStore';
import { Download, FileText, Share2, Search } from 'lucide-react';

export const ResultsPanel: React.FC = () => {
  const { result, status } = useWorkbenchStore();

  const actions = (
    <>
      <button className="flex items-center gap-1.5 px-2 py-1 text-[var(--t3)] hover:text-[var(--t2)] transition-colors">
        <Download size={14} />
        <span className="text-[9px] font-medium uppercase tracking-wider">CSV</span>
      </button>
      <button className="flex items-center gap-1.5 px-2 py-1 text-[var(--t3)] hover:text-[var(--t2)] transition-colors">
        <FileText size={14} />
        <span className="text-[9px] font-medium uppercase tracking-wider">XLSX</span>
      </button>
      <div className="w-[1px] h-3 bg-[var(--bd)] mx-1" />
      <button className="p-1 text-[var(--t3)] hover:text-[var(--t2)] transition-colors">
        <Share2 size={14} />
      </button>
    </>
  );

  if (status === 'executing') {
    return (
      <div className="flex-1 flex flex-col bg-[var(--bg2)] overflow-hidden">
        <PanelHeader title="Execution results" />
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <div className="flex gap-1.5">
             <div className="w-1 h-1 bg-[var(--amber)] animate-[blink_1s_infinite_0ms]" />
             <div className="w-1 h-1 bg-[var(--amber)] animate-[blink_1s_infinite_200ms]" />
             <div className="w-1 h-1 bg-[var(--amber)] animate-[blink_1s_infinite_400ms]" />
          </div>
          <span className="text-[10px] text-[var(--t3)] uppercase tracking-[0.15em]">Executing Query...</span>
        </div>
      </div>
    );
  }

  if (!result || result.length === 0) {
    return (
      <div className="flex-1 flex flex-col bg-[var(--bg2)] overflow-hidden">
        <PanelHeader title="Execution results" />
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center gap-3">
          <Search size={24} className="text-[var(--t4)]" />
          <p className="text-[10px] text-[var(--t3)] uppercase tracking-widest leading-relaxed">
            Ready for execution
          </p>
        </div>
      </div>
    );
  }

  const columns = Object.keys(result[0]);

  return (
    <div className="flex-1 flex flex-col bg-[var(--bg2)] overflow-hidden">
      <PanelHeader 
        title="Execution results" 
        tags={<Tag label={`${result.length} rows`} variant="blue" />}
        actions={actions}
      />
      <div className="flex-1 overflow-auto bg-[var(--bg0)]">
        <table className="w-full border-collapse text-[10px]">
          <thead className="sticky top-0 bg-[var(--bg1)] z-10 shadow-[0_1px_0_var(--bd)]">
            <tr>
              <th className="w-10 px-2 py-2 text-center text-[var(--t4)] font-medium border-r border-[var(--bd)]">#</th>
              {columns.map((col) => (
                <th 
                  key={col} 
                  className="px-4 py-2 text-left text-[var(--t3)] font-medium uppercase tracking-[0.08em] border-r border-[var(--bd)]"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.map((row, i) => (
              <tr 
                key={i} 
                className="border-b border-[var(--bd)] hover:bg-[var(--bg3)] transition-colors group"
              >
                <td className="w-10 px-2 py-1.5 text-center text-[var(--t4)] font-mono border-r border-[var(--bd)]">
                  {i + 1}
                </td>
                {columns.map((col) => {
                  const val = row[col];
                  const isMasked = typeof val === 'string' && val.includes('[ masked · PII ]');
                  const isNumber = typeof val === 'number';

                  return (
                    <td 
                      key={col} 
                      className={`px-4 py-1.5 border-r border-[var(--bd)] font-mono ${
                        isMasked ? 'text-[var(--t3)] italic' : 'text-[var(--t1)]'
                      } ${isNumber ? 'text-right text-[var(--blue-t)] font-medium' : ''}`}
                    >
                      {val}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

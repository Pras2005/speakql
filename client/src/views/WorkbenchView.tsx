import React, { useEffect } from 'react';
import { SQLEditor } from '../components/workbench/SQLEditor';
import { ContextPanel } from '../components/workbench/ContextPanel';
import { ResultsPanel } from '../components/workbench/ResultsPanel';
import { PromptBar } from '../components/workbench/PromptBar';
import { useWorkbenchStore } from '../store/workbenchStore';
import { MOCK_SQL, MOCK_RESULTS, MOCK_EXPLAINABILITY } from '../data/mockWorkbench';

export const WorkbenchView: React.FC = () => {
  const { status, setSql, setResult, setExplainability, setStatus } = useWorkbenchStore();

  // Initial load effect
  useEffect(() => {
    setSql(MOCK_SQL);
  }, [setSql]);

  // Mock execution effect
  useEffect(() => {
    if (status === 'generating') {
      const timer = setTimeout(() => {
        setStatus('idle');
      }, 1500);
      return () => clearTimeout(timer);
    }

    if (status === 'executing') {
      const timer = setTimeout(() => {
        setResult(MOCK_RESULTS);
        setExplainability(MOCK_EXPLAINABILITY);
        setStatus('success');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [status, setResult, setExplainability, setStatus]);

  return (
    <div className="h-full w-full flex flex-col bg-[var(--bg0)] overflow-hidden">
      <div className="flex-1 flex overflow-hidden">
        <SQLEditor />
        <ContextPanel />
      </div>
      <div className="h-[35%] min-h-[200px] border-t border-[var(--bd)] flex overflow-hidden">
        <ResultsPanel />
      </div>
      <PromptBar />
    </div>
  );
};

import React from 'react';
import { PanelHeader } from '../shared/PanelHeader';
import { SectionLabel } from '../shared/SectionLabel';
import { RiskBar } from './RiskBar';
import { useWorkbenchStore } from '../../store/workbenchStore';
import { Info, ShieldAlert, History, Key } from 'lucide-react';

export const ContextPanel: React.FC = () => {
  const { explainability, status } = useWorkbenchStore();

  if (!explainability && status === 'idle') {
    return (
      <div className="w-[340px] flex flex-col shrink-0 overflow-hidden">
        <PanelHeader title="Context analysis" />
        <div className="flex-1 bg-[var(--bg2)] flex flex-col items-center justify-center p-8 text-center">
          <Info size={24} className="text-[var(--t4)] mb-3" />
          <p className="text-[10px] text-[var(--t3)] uppercase tracking-wider leading-relaxed">
            Execute a query to see<br />governance and risk analysis
          </p>
        </div>
      </div>
    );
  }

  const { risk_score, flags, sql_rationale, policy_outcome } = explainability || {};

  return (
    <div className="w-[340px] flex flex-col shrink-0 overflow-hidden border-l border-[var(--bd)]">
      <PanelHeader title="Context analysis" />
      <div className="flex-1 bg-[var(--bg2)] overflow-y-auto p-4 space-y-6">
        
        {/* Risk Analysis Section */}
        <section className="space-y-3">
          <SectionLabel className="flex items-center gap-2">
            <ShieldAlert size={10} />
            Risk score analysis
          </SectionLabel>
          <div className="bg-[var(--bg3)] border border-[var(--bd2)] p-3 space-y-3">
            <div className="flex items-end justify-between">
              <span className="text-[20px] font-medium leading-none tabular-nums" style={{ color: 'var(--amber)' }}>
                {risk_score || 0}
              </span>
              <span className="text-[9px] text-[var(--t3)] font-medium uppercase tracking-wider">
                out of 100
              </span>
            </div>
            <RiskBar score={risk_score || 0} />
            <div className="flex flex-wrap gap-1.5 pt-1">
              {flags?.map((flag: string) => (
                <span key={flag} className="px-1.5 py-0.5 bg-[var(--red-bg)] text-[var(--red-t)] text-[9px] border border-[var(--red-bd)] font-medium uppercase tracking-tight">
                  {flag.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Semantic Context */}
        <section className="space-y-3">
          <SectionLabel className="flex items-center gap-2">
            <Info size={10} />
            Natural language rationale
          </SectionLabel>
          <div className="text-[10px] text-[var(--t2)] leading-relaxed font-sans italic border-l-2 border-[var(--bd2)] pl-3">
            {sql_rationale || 'Generating rationale...'}
          </div>
        </section>

        {/* Policy Section */}
        <section className="space-y-3">
          <SectionLabel className="flex items-center gap-2">
            <Key size={10} />
            Policy compliance
          </SectionLabel>
          <div className="space-y-2">
             {policy_outcome?.rules_applied?.map((rule: string) => (
               <div key={rule} className="flex items-center justify-between p-2 bg-[var(--bg3)] border border-[var(--bd)]">
                 <span className="text-[9px] text-[var(--t2)] uppercase tracking-tight">{rule.replace(/_/g, ' ')}</span>
                 <span className="text-[9px] text-[var(--green-t)] font-medium uppercase">Active</span>
               </div>
             ))}
          </div>
        </section>

        {/* Audit Trail Section Placeholder */}
        <section className="space-y-3">
          <SectionLabel className="flex items-center gap-2">
            <History size={10} />
            Audit trail
          </SectionLabel>
          <div className="space-y-2">
            <div className="text-[9px] text-[var(--t3)] uppercase tracking-widest text-center py-4 border border-dashed border-[var(--bd)]">
              NO PRIOR RUNS RECORDED
            </div>
          </div>
        </section>

      </div>
    </div>
  );
};

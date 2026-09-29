import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Shell } from './components/layout/Shell';
import { WorkbenchView } from './views/WorkbenchView';
import { AuditView, CatalogView, PolicyView } from './views/Placeholders';

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Shell />}>
          <Route path="/" element={<WorkbenchView />} />
          <Route path="/audit" element={<AuditView />} />
          <Route path="/catalog" element={<CatalogView />} />
          <Route path="/policy" element={<PolicyView />} />
          <Route path="/approvals" element={<div className="p-8 text-[var(--t3)] uppercase tracking-widest">Approvals View Placeholder</div>} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;

import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { authApi } from '@/api/auth';
import { useSessionStore } from '@/store/session';
import { Button } from '@/components/ui/Button';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const setSessionToken = useSessionStore((state) => state.setSessionToken);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const loginMutation = useMutation({
    mutationFn: async () => (await authApi.login({ username, password })).data,
    onSuccess: async (data) => {
      setSessionToken(data.access_token);
      await queryClient.invalidateQueries({ queryKey: ['session-bootstrap'] });
      navigate(location.state?.from ?? '/workbench', { replace: true });
    },
    onError: () => {
      toast.error('Login failed. Check your credentials and workspace membership.');
    },
  });

  return (
    <div className="auth-shell">
      <section className="auth-hero">
        <div className="auth-kicker">Governed data access</div>
        <h1 className="auth-title">Turn natural language into controlled SQL.</h1>
        <p className="auth-copy">
          The new client is built around visible grant boundaries. Every connector, export, and schema surface now reflects the active workspace and the database-level access actually returned by the backend.
        </p>
        <div className="auth-grid">
          <div className="auth-stat">
            <strong>Two-layer security</strong>
            Workspace role plus per-database grant.
          </div>
          <div className="auth-stat">
            <strong>Capability-aware UI</strong>
            Query, export, and manage actions are visible without pretending they are all allowed.
          </div>
          <div className="auth-stat">
            <strong>Audit-first workflows</strong>
            Query generation, execution, approval, and export stay inside the governed path.
          </div>
          <div className="auth-stat">
            <strong>Workspace reset on switch</strong>
            Cache and selected database state re-align when tenancy changes.
          </div>
        </div>
      </section>

      <section className="auth-panel-wrap">
        <div className="auth-panel">
          <div className="eyebrow">Access workspace</div>
          <h2 style={{ marginTop: '0.65rem' }}>Sign in</h2>
          <p className="muted">Use your SpeakQL credentials. The backend resolves your first active workspace on login.</p>

          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              loginMutation.mutate();
            }}
          >
            <div className="field">
              <label htmlFor="username">Username</label>
              <input id="username" className="input" value={username} onChange={(event) => setUsername(event.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input id="password" className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            <Button type="submit" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? 'Signing in...' : 'Enter workspace'}
            </Button>
          </form>

          <div className="link-row">
            <span>Need a new tenant footprint?</span>
            <Link to="/signup">Create an account</Link>
          </div>
        </div>
      </section>
    </div>
  );
}

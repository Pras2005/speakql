import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

import { authApi } from '@/api/auth';
import { Button } from '@/components/ui/Button';

export function SignupPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const signupMutation = useMutation({
    mutationFn: async () => authApi.signup({ username, password }),
    onSuccess: () => {
      toast.success('Account created. Sign in to enter your default workspace.');
      navigate('/login');
    },
    onError: () => {
      toast.error('Signup failed. Try a different username.');
    },
  });

  return (
    <div className="auth-shell">
      <section className="auth-hero">
        <div className="auth-kicker">Provision tenancy</div>
        <h1 className="auth-title">Start with a default organization and workspace.</h1>
        <p className="auth-copy">
          Signup provisions the initial tenant context so the frontend can bootstrap into a valid workspace immediately after authentication.
        </p>
      </section>

      <section className="auth-panel-wrap">
        <div className="auth-panel">
          <div className="eyebrow">Create access</div>
          <h2 style={{ marginTop: '0.65rem' }}>New account</h2>
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              signupMutation.mutate();
            }}
          >
            <div className="field">
              <label htmlFor="signup-username">Username</label>
              <input id="signup-username" className="input" value={username} onChange={(event) => setUsername(event.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="signup-password">Password</label>
              <input id="signup-password" className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            <Button type="submit" disabled={signupMutation.isPending}>
              {signupMutation.isPending ? 'Creating...' : 'Create account'}
            </Button>
          </form>

          <div className="link-row">
            <span>Already have a workspace context?</span>
            <Link to="/login">Sign in</Link>
          </div>
        </div>
      </section>
    </div>
  );
}

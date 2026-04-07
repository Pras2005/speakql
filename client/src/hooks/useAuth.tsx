import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { apiClient, getErrorMessage } from '@/lib/api';
import { authStorage } from '@/lib/auth';

type UseAuthReturns = {
  requestLogin: (username: string, password: string) => Promise<void>;
  requestSignup: (username: string, password: string) => Promise<void>;
  requestLogout: () => void;
  isLoggedIn: () => boolean;
};

function useAuth(): UseAuthReturns {
  const navigate = useNavigate();

  const requestLogin = async (username: string, password: string) => {
    try {
      const res = await apiClient.login(username, password);
      authStorage.setToken(res.data.access_token);

      toast.success(`Welcome back, ${username}!`);
      navigate('/chat');
    } catch (error) {
      toast.error(getErrorMessage(error) || 'Login failed. Please check your credentials.');
      console.log(error);
    }
  };

  const requestSignup = async (username: string, password: string) => {
    try {
      await apiClient.signup(username, password);

      toast.success('Signup successful! You can now log in.');
      navigate('/login');
    } catch (error) {
      toast.error(getErrorMessage(error) || 'Signup failed. Try a different username.');
      console.log(error);
    }
  };

  const requestLogout = () => {
    authStorage.clearToken();

    toast('Logged out successfully.', {
      description: 'Hope to see you again soon!',
    });

    navigate('/login');
  };

  const isLoggedIn = () => {
    return authStorage.isAuthenticated();
  };

  return {
    requestLogin,
    requestSignup,
    requestLogout,
    isLoggedIn,
  };
}

export default useAuth;

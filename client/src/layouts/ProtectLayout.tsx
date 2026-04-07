import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Outlet } from 'react-router-dom';
import { authStorage } from '@/lib/auth';

const ProtectLayout = () => {
  const navigate = useNavigate();

  const isLoggedIn = () => {
    return authStorage.isAuthenticated();
  };

  useEffect(() => {
    if (!isLoggedIn()) {
      navigate('/login');
    }
  }, [navigate]);

  return isLoggedIn() ? <Outlet /> : null;
};

export default ProtectLayout;

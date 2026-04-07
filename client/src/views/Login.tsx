import { useState, useEffect, type FormEvent } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import useAuth from '@/hooks/useAuth';
import { Link } from 'react-router-dom';
import { Database, KeyRound } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const { requestLogin } = useAuth();

  // Load saved credentials on initial render if remember me was used
  useEffect(() => {
    const savedUsername = localStorage.getItem('rememberedUsername');
    const savedRememberMe = localStorage.getItem('rememberMe') === 'true';
    
    if (savedRememberMe && savedUsername) {
      setUsername(savedUsername);
      setRememberMe(true);
    }
  }, []);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // Save or remove credentials based on remember me state
    if (rememberMe) {
      localStorage.setItem('rememberedUsername', username);
      localStorage.setItem('rememberMe', 'true');
    } else {
      localStorage.removeItem('rememberedUsername');
      localStorage.removeItem('rememberMe');
    }
    
    void requestLogin(username, password);
  };
  
  return (
    <div className="flex items-center justify-center h-screen w-screen bg-gradient-to-br from-gray-900 to-gray-800 relative overflow-hidden">
      {/* Enhanced background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 right-0 w-full h-full">
          <svg width="100%" height="100%" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="none" />
            <path d="M0 0L50 50M100 0L0 100M150 0L0 150M200 0L0 200M250 0L0 250M300 0L0 300" 
                  stroke="#4f46e5" strokeWidth="1" fill="none" opacity="0.2" />
            <path d="M0 0L50 50M100 0L0 100M150 0L0 150M200 0L0 200M250 0L0 250M300 0L0 300" 
                  stroke="#3b82f6" strokeWidth="1" fill="none" opacity="0.2" 
                  transform="translate(100, 0)" />
          </svg>
        </div>
      </div>
      
      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full"
            style={{
              width: Math.random() * 10 + 5,
              height: Math.random() * 10 + 5,
              background: `rgba(${Math.random() * 100 + 79}, ${Math.random() * 100 + 70}, ${Math.random() * 200 + 55}, 0.3)`,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`
            }}
            animate={{
              y: [0, -30, 0],
              opacity: [0.4, 0.8, 0.4]
            }}
            transition={{
              duration: Math.random() * 5 + 10,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        ))}
      </div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-gray-800 backdrop-blur-sm backdrop-filter shadow-2xl rounded-2xl p-10 w-full max-w-md space-y-6 border border-gray-700/50 relative z-10"
        style={{ boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.15)' }}
      >
        <div className="flex flex-col items-center mb-6">
          <motion.div 
            className="flex items-center gap-3 mb-3"
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <div className="bg-indigo-900/80 p-3 rounded-full shadow-lg shadow-indigo-900/30">
              <Database className="text-indigo-300 w-6 h-6" />
            </div>
            <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 to-blue-300">SpeakQL</h2>
          </motion.div>
          <p className="text-gray-400 text-sm">Login to your account</p>
        </div>
        
        <form className="space-y-5" onSubmit={handleSubmit}>
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Username</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                <KeyRound className="w-4 h-4" />
              </span>
              <Input
                type="text"
                placeholder="Enter your username"
                className="pl-10 bg-gray-700/60 border-gray-600 text-gray-200 placeholder-gray-500 focus:border-indigo-500 focus:ring-indigo-500 rounded-lg"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
            <Input
              type="password"
              placeholder="Enter your password"
              className="bg-gray-700/60 border-gray-600 text-gray-200 placeholder-gray-500 focus:border-indigo-500 focus:ring-indigo-500 rounded-lg"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </motion.div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-400 cursor-pointer">
                Remember me
              </label>
            </div>
            <motion.div 
              className="text-sm"
              whileHover={{ scale: 1.05 }}
            >
              <a href="#" className="text-indigo-400 hover:text-indigo-300 transition duration-200">
                Forgot password?
              </a>
            </motion.div>
          </div>
          
          <motion.div
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white rounded-lg py-6 mt-6 shadow-lg shadow-indigo-700/30"
            >
              Sign In
            </Button>
          </motion.div>
        </form>
        
        <motion.p 
          className="text-center text-sm text-gray-400 mt-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          Don't have an account?{' '}
          <Link to="/signup" className="text-indigo-400 hover:text-indigo-300 hover:underline transition duration-200 font-medium">
            Sign up
          </Link>
        </motion.p>
      </motion.div>
    </div>
  );
}

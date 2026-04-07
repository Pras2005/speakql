import { useState, type FormEvent } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import useAuth from '@/hooks/useAuth';
import { Database } from 'lucide-react';
import { toast } from 'sonner';

export default function SignupPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const { requestSignup } = useAuth();
  
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error('Passwords do not match.');
      return;
    }

    void requestSignup(username, password);
  };
  
  return (
    <div className="flex items-center justify-center h-screen w-screen bg-gray-900 relative">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 overflow-hidden opacity-20">
        <div className="absolute top-0 right-0 w-full h-full">
          <svg width="100%" height="100%" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="none" />
            <path d="M0 0L50 50M100 0L0 100M150 0L0 150M200 0L0 200M250 0L0 250M300 0L0 300" 
                  stroke="#4f46e5" strokeWidth="1" fill="none" opacity="0.3" />
            <path d="M0 0L50 50M100 0L0 100M150 0L0 150M200 0L0 200M250 0L0 250M300 0L0 300" 
                  stroke="#3b82f6" strokeWidth="1" fill="none" opacity="0.3" 
                  transform="translate(100, 0)" />
          </svg>
        </div>
      </div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="bg-gray-800 shadow-2xl rounded-2xl p-10 w-full max-w-md space-y-6 border border-gray-700 relative z-10"
      >
        <div className="flex flex-col items-center mb-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-indigo-900 p-2 rounded-full">
              <Database className="text-indigo-300 w-6 h-6" />
            </div>
            <h2 className="text-3xl font-bold text-indigo-300">SpeakQL</h2>
          </div>
          <p className="text-gray-400 text-sm">Create your account</p>
        </div>
        
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-300">Username</label>
            <Input
              type="text"
              placeholder="Choose a username"
              className="mt-1 bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-500 focus:border-indigo-500 focus:ring-indigo-500"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">Password</label>
            <Input
              type="password"
              placeholder="Create a password"
              className="mt-1 bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-500 focus:border-indigo-500 focus:ring-indigo-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">Confirm Password</label>
            <Input
              type="password"
              placeholder="Confirm your password"
              className="mt-1 bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-500 focus:border-indigo-500 focus:ring-indigo-500"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
          
          <div className="flex items-center">
            <input
              id="terms"
              name="terms"
              type="checkbox"
              className="h-4 w-4 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="terms" className="ml-2 block text-sm text-gray-400">
              I agree to the <a href="#" className="text-indigo-400 hover:text-indigo-300">Terms of Service</a> and <a href="#" className="text-indigo-400 hover:text-indigo-300">Privacy Policy</a>
            </label>
          </div>
          
          <Button
            type="submit"
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg py-6 mt-4"
          >
            Create Account
          </Button>
        </form>
        
        <p className="text-center text-sm text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300 hover:underline">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

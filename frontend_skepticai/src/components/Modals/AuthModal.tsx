import React, { useState } from 'react';
import { X, Mail, Lock, User, Check, ArrowRight, Loader2 } from 'lucide-react';
import { UserProfile } from '../../types.ts';
import { BrandLogo } from '../BrandLogo.tsx';
import { signup, login, AuthResponse } from '../../services/apiService.ts';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (profile: UserProfile) => void;
  initialMode?: 'signin' | 'signup';
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onLogin,
  initialMode = 'signin'
}) => {
  const [mode, setMode] = useState<'signin' | 'signup'>(initialMode);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (mode === 'signup') {
      if (!name.trim()) {
        setError('Please enter your full name.');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
    }

    if (!email.includes('@') || password.length < 6) {
      setError('Please enter a valid email and a password with at least 6 characters.');
      return;
    }

    setLoading(true);

    try {
      let response: AuthResponse;
      
      if (mode === 'signup') {
        response = await signup({ name, email, password });
      } else {
        response = await login({ email, password });
      }

      setSuccess(mode === 'signup' ? 'Account created successfully!' : 'Signed in successfully!');
      
      // Convert backend user to frontend UserProfile
      const profile: UserProfile = {
        id: response.user.id,
        name: response.user.name,
        email: response.user.email,
        role: response.user.role,
        isLoggedIn: true
      };

      setTimeout(() => {
        onLogin(profile);
        onClose();
      }, 600);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Authentication failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    // For now, keep the mock Google sign-in as a demo fallback
    const profile: UserProfile = {
      id: `usr_google_${Date.now()}`,
      name: 'Dr. Sarah Connor',
      email: 'sarah.connor@skepticai.research',
      role: 'Principal Verification Scientist',
      isLoggedIn: true
    };
    onLogin(profile);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-md rounded-2xl bg-[#141416] border border-gray-800 shadow-2xl p-6 text-gray-200 overflow-hidden">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          disabled={loading}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer disabled:opacity-50"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Brand Header */}
        <div className="text-center mb-6">
          <BrandLogo size="lg" className="justify-center mb-2" />
          <p className="text-xs text-gray-400 mt-1">
            Access your verified hallucination audits and cross-model history
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex p-1 rounded-xl bg-black/40 border border-gray-800 mb-5">
          <button
            type="button"
            onClick={() => { setMode('signin'); setError(null); setSuccess(null); }}
            disabled={loading}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer disabled:opacity-50 ${
              mode === 'signin'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setMode('signup'); setError(null); setSuccess(null); }}
            disabled={loading}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer disabled:opacity-50 ${
              mode === 'signup'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Error / Success Notifications */}
        {error && (
          <div className="mb-4 p-2.5 rounded-lg bg-red-950/40 border border-red-500/50 text-red-300 text-xs flex items-center gap-2 animate-in slide-in-from-top-2 duration-200">
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="mb-4 p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/50 text-emerald-300 text-xs flex items-center gap-2 animate-in slide-in-from-top-2 duration-200">
            <Check className="w-4 h-4" />
            <span>{success}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  required
                  disabled={loading}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Dr. Alex Morgan"
                  className="w-full pl-9 pr-3 py-2 rounded-xl bg-black/40 border border-gray-800 focus:border-blue-500 focus:outline-none text-xs text-white placeholder:text-gray-500 disabled:opacity-50"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                disabled={loading}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@organization.com"
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-black/40 border border-gray-800 focus:border-blue-500 focus:outline-none text-xs text-white placeholder:text-gray-500 disabled:opacity-50"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                disabled={loading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-black/40 border border-gray-800 focus:border-blue-500 focus:outline-none text-xs text-white placeholder:text-gray-500 disabled:opacity-50"
              />
            </div>
          </div>

          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">Confirm Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
                <input
                  type="password"
                  required
                  disabled={loading}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 rounded-xl bg-black/40 border border-gray-800 focus:border-blue-500 focus:outline-none text-xs text-white placeholder:text-gray-500 disabled:opacity-50"
                />
              </div>
            </div>
          )}

          {mode === 'signin' && (
            <div className="flex items-center justify-between text-xs text-gray-400">
              <label className="flex items-center gap-1.5 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  disabled={loading}
                  className="rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-0 cursor-pointer"
                />
                <span>Remember me</span>
              </label>
              <button
                type="button"
                onClick={() => alert('Password reset instructions will be sent to your registered email.')}
                disabled={loading}
                className="text-blue-400 hover:underline cursor-pointer disabled:opacity-50"
              >
                Forgot password?
              </button>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition cursor-pointer shadow-lg shadow-blue-900/40 flex items-center justify-center gap-1.5 mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>{mode === 'signin' ? 'Signing in...' : 'Creating account...'}</span>
              </>
            ) : (
              <>
                <span>{mode === 'signin' ? 'Sign In to SkepticAI' : 'Create Free Account'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-800" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-[#141416] px-2 text-gray-500 text-[10px] font-semibold">Or continue with</span>
          </div>
        </div>

        {/* Google Sign In Button */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full py-2 rounded-xl bg-black/40 hover:bg-white/5 border border-gray-800 text-gray-200 font-medium text-xs transition cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span>Continue with Google</span>
        </button>

        <p className="text-[10px] text-gray-500 text-center mt-4">
          Prototype environment: authentication is managed securely locally.
        </p>
      </div>
    </div>
  );
};
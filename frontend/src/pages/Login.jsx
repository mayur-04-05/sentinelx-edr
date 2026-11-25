import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Eye, EyeOff, Lock, User, UserPlus } from 'lucide-react';

export default function Login() {
  const { login, register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState('Analyst');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);

  // If already authenticated, redirect to dashboard automatically
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');
    
    if (!username || !password) {
      setError('Please fill in all fields.');
      return;
    }

    setLoading(true);

    try {
      if (isRegistering) {
        if (password !== confirmPassword) {
          setError('Passwords do not match.');
          setLoading(false);
          return;
        }
        const regRes = await register(username, password, selectedRole);
        if (regRes.success) {
          setInfo('Account created! Logging you in...');
          const loginRes = await login(username, password);
          if (loginRes.success) {
            navigate('/dashboard', { replace: true });
            return;
          } else {
            setIsRegistering(false);
            setPassword('');
            setConfirmPassword('');
          }
        } else {
          setError(regRes.error);
        }
      } else {
        const loginRes = await login(username, password);
        if (loginRes.success) {
          navigate('/dashboard', { replace: true });
          return;
        } else {
          setError(loginRes.error);
        }
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bgDark flex flex-col items-center justify-center p-4">
      {/* Glow effect background */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-md bg-bgCard border border-borderDark rounded-xl p-8 shadow-2xl relative z-10">
        {/* EDR Platform Logo Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg text-accentBlue mb-3 animate-pulse">
            <Shield size={36} />
          </div>
          <h1 className="text-2xl font-bold tracking-wider text-textPrimary">SENTINELX EDR</h1>
          <p className="text-xs text-textSecondary mt-1 uppercase tracking-widest">Detect. Investigate. Respond.</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-accentRed/10 border border-accentRed/30 rounded text-accentRed text-sm text-center">
            {error}
          </div>
        )}

        {info && (
          <div className="mb-4 p-3 bg-accentGreen/10 border border-accentGreen/30 rounded text-accentGreen text-sm text-center">
            {info}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-2">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-bgInput border border-borderDark rounded-lg py-2.5 pl-10 pr-4 text-textPrimary focus:outline-none focus:border-accentBlue focus:ring-1 focus:ring-accentBlue transition duration-200 text-sm"
                placeholder="Username"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-2">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-bgInput border border-borderDark rounded-lg py-2.5 pl-10 pr-10 text-textPrimary focus:outline-none focus:border-accentBlue focus:ring-1 focus:ring-accentBlue transition duration-200 text-sm"
                placeholder="Password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-textSecondary hover:text-textPrimary"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {isRegistering && (
            <>
              <div>
                <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-2">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={18} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full bg-bgInput border border-borderDark rounded-lg py-2.5 pl-10 pr-4 text-textPrimary focus:outline-none focus:border-accentBlue focus:ring-1 focus:ring-accentBlue transition duration-200 text-sm"
                    placeholder="Confirm password"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-2">Role Assignment</label>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="w-full bg-bgInput border border-borderDark rounded-lg py-2.5 px-3 text-textPrimary focus:outline-none focus:border-accentBlue transition duration-200 text-sm"
                >
                  <option value="Analyst">Security Analyst</option>
                  <option value="Viewer">Viewer (Read-Only)</option>
                  <option value="Admin">System Administrator</option>
                </select>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accentBlue hover:bg-blue-600 text-white py-2.5 rounded-lg font-semibold text-sm transition duration-200 shadow-md flex items-center justify-center gap-2 cursor-pointer mt-6"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : isRegistering ? (
              <>
                <UserPlus size={18} />
                Create Account
              </>
            ) : (
              <>
                <Shield size={18} />
                Access Platform
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-textSecondary">
          {isRegistering ? (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(false);
                  setError('');
                }}
                className="text-accentBlue hover:underline font-semibold"
              >
                Log In
              </button>
            </p>
          ) : (
            <p>
              New analyst?{' '}
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(true);
                  setError('');
                }}
                className="text-accentBlue hover:underline font-semibold"
              >
                Request Registration
              </button>
            </p>
          )}
        </div>
      </div>
      <p className="mt-8 text-center text-[10px] text-textSecondary/50 uppercase tracking-widest">
        First-user registration seeds platform administrator account.
      </p>
    </div>
  );
}

/**
 * AgroPulse AI - Login Page
 * Mobile-first, accessible login form with Cognito integration
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { Leaf, Lock, Mail, Eye, EyeOff, Loader2 } from 'lucide-react';
import { authAPI } from '../services/api';

const loginSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      const tokens = await authAPI.login(data.username, data.password);
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('id_token', tokens.id_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      toast.success('Welcome back! Loading your farm dashboard...');
      navigate('/dashboard');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  // Demo login (bypasses auth for hackathon demo)
  const handleDemoLogin = () => {
    localStorage.setItem('access_token', 'demo_token');
    localStorage.setItem('farmer_name', 'Ramesh Kumar');
    toast.success('Demo mode activated!');
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-agro-green-600 via-agro-green-700 to-agro-earth-700 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-10 left-10 w-40 h-40 bg-white rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-60 h-60 bg-agro-earth-400 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-white rounded-2xl shadow-xl mb-4">
            <Leaf className="w-10 h-10 text-agro-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-white">AgroPulse AI</h1>
          <p className="text-agro-green-100 mt-1">Smart Farming Intelligence</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 animate-slide-up">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6">Welcome Back</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email or Username
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  {...register('username')}
                  type="text"
                  placeholder="farmer@example.com"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-500 focus:border-transparent outline-none transition"
                />
              </div>
              {errors.username && (
                <p className="text-red-500 text-sm mt-1">{errors.username.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-500 focus:border-transparent outline-none transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
              )}
            </div>

            {/* Login Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-agro-green-600 hover:bg-agro-green-700 disabled:bg-gray-300 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-sm text-gray-400">or</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          {/* Demo Login */}
          <button
            onClick={handleDemoLogin}
            className="w-full py-3 border-2 border-agro-green-500 text-agro-green-700 font-semibold rounded-xl hover:bg-agro-green-50 transition-colors"
          >
            Try Demo (No Login Required)
          </button>

          {/* Language Note */}
          <p className="text-center text-xs text-gray-400 mt-4">
            Supports English • हिंदी • मराठी • తెలుగు • ಕನ್ನಡ
          </p>
        </div>

        {/* Footer */}
        <p className="text-center text-agro-green-200 text-sm mt-6">
          Powered by AWS Bedrock + SageMaker
        </p>
      </div>
    </div>
  );
};

export default LoginPage;

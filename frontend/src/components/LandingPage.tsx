/**
 * LandingPage Component
 * Cinematic ocean-themed landing page with login
 */

import React, { useState } from 'react';

interface LandingPageProps {
  onLogin: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      onLogin();
    }, 800);
  };

  return (
    <div className="landing-page relative w-full min-h-screen overflow-hidden bg-black">
      {/* Animated Background */}
      <div className="absolute inset-0">
        {/* Deep Ocean Gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-950 via-blue-900 to-slate-950" />
        
        {/* Animated Waves */}
        <div className="absolute inset-0">
          <svg className="absolute inset-0 w-full h-full opacity-30" preserveAspectRatio="none" viewBox="0 0 1200 120">
            <defs>
              <linearGradient id="wave-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#0284c7" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path
              d="M0,50 Q300,0 600,50 T1200,50 L1200,120 L0,120 Z"
              fill="url(#wave-gradient)"
              className="wave-animation"
            />
            <path
              d="M0,60 Q300,20 600,60 T1200,60 L1200,120 L0,120 Z"
              fill="#0ea5e9"
              opacity="0.1"
              className="wave-animation-slow"
            />
          </svg>
        </div>

        {/* Floating Particles */}
        <div className="absolute inset-0">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-cyan-400 rounded-full opacity-60 particle-float"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${i * 0.2}s`,
              }}
            />
          ))}
        </div>

        {/* Glow Orbs */}
        <div className="absolute top-20 left-10 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute -top-40 right-10 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute -bottom-8 left-1/2 w-96 h-96 bg-teal-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-center justify-between min-h-screen px-8">
        {/* Left Section - Hero Content */}
        <div className="flex-1 max-w-2xl">
          <div className="fade-in-up">
            {/* Logo */}
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-2xl">🌊</span>
              </div>
              <span className="text-white font-bold text-2xl tracking-tight">ORCA</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-6xl font-bold text-white mb-6 leading-tight">
              Smarter Decisions
              <br />
              <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                for Safer Seas
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-blue-200 mb-8 leading-relaxed">
              ORCA is a multi-agent marine ecosystem reasoning system that helps fishermen and coastal communities find safe, suitable and productive fishing zones through real-time data analysis and collaborative intelligence.
            </p>

            {/* Features */}
            <div className="grid grid-cols-3 gap-6 mb-12">
              <div className="feature-card">
                <div className="text-cyan-400 text-2xl mb-2">⚡</div>
                <p className="text-sm text-blue-200">Real-time<br />Marine Data</p>
              </div>
              <div className="feature-card">
                <div className="text-cyan-400 text-2xl mb-2">🤖</div>
                <p className="text-sm text-blue-200">AI-Powered<br />Recommendations</p>
              </div>
              <div className="feature-card">
                <div className="text-cyan-400 text-2xl mb-2">🛡️</div>
                <p className="text-sm text-blue-200">Safety<br />First</p>
              </div>
            </div>

            {/* CTA Button */}
            <button
              onClick={() => document.getElementById('login-form')?.scrollIntoView({ behavior: 'smooth' })}
              className="px-8 py-4 bg-gradient-to-r from-cyan-400 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-cyan-400/50 transition-all duration-300 transform hover:scale-105"
            >
              Get Started →
            </button>
          </div>
        </div>

        {/* Right Section - Login Card */}
        <div className="flex-1 flex items-center justify-center">
          <div
            id="login-form"
            className="w-full max-w-md glassmorphic-card p-8 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-2xl"
          >
            {/* Card Header */}
            <h2 className="text-2xl font-bold text-white mb-2">Welcome Back</h2>
            <p className="text-blue-200 text-sm mb-8">Sign in to access your ocean insights</p>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-6">
              {/* Email Input */}
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-2">
                  Email address
                </label>
                <input
                  type="email"
                  placeholder="captain@orca.seas"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all duration-300 backdrop-blur-sm"
                />
              </div>

              {/* Password Input */}
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300/50 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition-all duration-300 backdrop-blur-sm"
                />
              </div>

              {/* Remember Me */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="remember"
                  className="w-4 h-4 accent-cyan-400"
                />
                <label htmlFor="remember" className="ml-2 text-sm text-blue-200">
                  Remember me
                </label>
              </div>

              {/* Login Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-gradient-to-r from-cyan-400 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg hover:shadow-cyan-400/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Logging in...' : 'Login'}
              </button>

              {/* Sign Up Link */}
              <p className="text-center text-blue-200 text-sm">
                Don't have an account?{' '}
                <span className="text-cyan-400 cursor-pointer hover:underline">Sign up</span>
              </p>
            </form>

            {/* Divider */}
            <div className="my-6 border-t border-white/20" />

            {/* Demo Note */}
            <p className="text-xs text-blue-300 text-center">
              For demo, use any email and password to continue
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, Loader2, LockKeyhole, Mail, Sprout } from 'lucide-react';
import { DEMO_USERS } from '../data/mockData';
import { User } from '../types';

const DEMO_CREDENTIALS: Record<string, string> = {
  'elena.vasconcelos@agriclimate-twin.org': 'Ceres2026!',
  'm.vance@agri-ai-lab.edu': 'Ceres2026!',
  'carlos.mendez@agrovalle.com': 'Ceres2026!',
  'sofia.morales@climateresilient.tech': 'Ceres2026!'
};

interface LoginScreenProps {
  onLoginSuccess: (user: User) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLoginSuccess }) => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [hasError, setHasError] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 400));

    const normalizedEmail = email.trim().toLowerCase();
    const user = DEMO_USERS.find((demoUser) => demoUser.email === normalizedEmail);

    if (user && DEMO_CREDENTIALS[normalizedEmail] === password) {
      setIsSubmitting(false);
      onLoginSuccess(user);
      return;
    }

    setHasError(true);
    setIsSubmitting(false);
  };

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex items-center justify-center px-4 py-10 selection:bg-emerald-500 selection:text-slate-950">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 rounded-[22px] bg-gradient-to-tr from-emerald-600 via-emerald-500 to-teal-400 p-0.5 shadow-xl shadow-emerald-500/20 flex items-center justify-center">
            <div className="w-full h-full bg-white dark:bg-slate-950 rounded-[20px] flex items-center justify-center">
              <Sprout className="w-8 h-8 text-emerald-500" />
            </div>
          </div>
          <h1 className="mt-5 text-2xl font-black tracking-tight">CeresPINN</h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{t('login.title')}</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl shadow-slate-200/50 dark:shadow-black/20"
        >
          <div className="space-y-5">
            <label className="block">
              <span className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">{t('login.emailLabel')}</span>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setHasError(false);
                  }}
                  autoComplete="email"
                  required
                  disabled={isSubmitting}
                  className="w-full pl-10 pr-3 py-3 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition"
                />
              </div>
            </label>

            <label className="block">
              <span className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">{t('login.passwordLabel')}</span>
              <div className="relative">
                <LockKeyhole className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value);
                    setHasError(false);
                  }}
                  autoComplete="current-password"
                  required
                  disabled={isSubmitting}
                  className="w-full pl-10 pr-11 py-3 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  disabled={isSubmitting}
                  aria-label={showPassword ? t('login.hidePassword') : t('login.showPassword')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-slate-400 hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors disabled:opacity-50"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </label>
          </div>

          {hasError && (
            <p role="alert" className="mt-4 text-sm text-rose-600 dark:text-rose-400">{t('login.error')}</p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-6 w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-[.99] text-white font-bold text-sm shadow-lg shadow-emerald-600/25 transition-all"
          >
            {isSubmitting ? <Loader2 className="mx-auto w-5 h-5 animate-spin" aria-hidden="true" /> : t('login.submit')}
          </button>
        </form>
      </div>
    </main>
  );
};

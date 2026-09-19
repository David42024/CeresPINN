import React, { FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Activity, CloudRain, Droplets, Eye, EyeOff, Globe, Leaf, Loader2, LockKeyhole, Mail, Moon, Sprout, Sun, Thermometer, TrendingUp } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { DEMO_USERS } from '../data/mockData';
import { User } from '../types';

const DEMO_CREDENTIALS: Record<string, string> = {
  'admin@agri.com': 'Ceres2026!',
  'm.vance@agri-ai-lab.edu': 'Ceres2026!',
  'carlos.mendez@agrovalle.com': 'Ceres2026!',
  'sofia.morales@climateresilient.tech': 'Ceres2026!'
};

interface LoginScreenProps {
  onLoginSuccess: (user: User) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLoginSuccess }) => {
  const { t, i18n } = useTranslation();
  const { theme, toggleTheme } = useTheme();
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
    <main className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex selection:bg-emerald-500 selection:text-slate-950">
      <section
        className="hidden md:flex md:w-[45%] min-h-screen relative overflow-hidden bg-gradient-to-br from-emerald-600 via-teal-500 to-slate-900 text-white p-10 lg:p-14 flex-col justify-between"
        style={{
          backgroundImage: 'radial-gradient(rgba(255,255,255,0.16) 1px, transparent 1px), linear-gradient(135deg, rgb(5 150 105), rgb(20 184 166), rgb(15 23 42))',
          backgroundSize: '22px 22px, 100% 100%'
        }}
      >
        <div className="relative z-10">
          <div className="flex items-center justify-between gap-3">
            <div className="w-20 h-20 rounded-[26px] bg-white/15 border border-white/25 backdrop-blur-sm flex items-center justify-center shadow-2xl">
              <Sprout className="w-11 h-11 text-emerald-50" />
            </div>
            <span className="bg-emerald-500/10 text-emerald-100 border border-emerald-400/30 rounded-full px-3 py-1 text-xs font-mono whitespace-nowrap backdrop-blur-sm">
              🌱 Simulación activa
            </span>
          </div>
          <div className="mt-7 flex items-center gap-3">
            <h1 className="text-3xl font-black tracking-tight">CeresPINN</h1>
            <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-100 font-bold border border-white/15">
              v2.5
            </span>
          </div>
          <p className="mt-6 max-w-sm text-lg leading-8 text-emerald-50/90 font-medium">{t('login.tagline')}</p>
        </div>

        <div className="relative z-10 max-w-md space-y-6">
          <div className="grid grid-cols-2 gap-x-6 gap-y-7">
            <div className="flex items-center gap-3">
              <Sprout className="w-5 h-5 text-emerald-100" />
              <span className="text-sm text-white/85">{t('login.feature1')}</span>
            </div>
            <div className="flex items-center gap-3">
              <Droplets className="w-5 h-5 text-cyan-100" />
              <span className="text-sm text-white/85">{t('login.feature2')}</span>
            </div>
            <div className="flex items-center gap-3">
              <CloudRain className="w-5 h-5 text-sky-100" />
              <span className="text-sm text-white/85">{t('login.feature3')}</span>
            </div>
            <div className="flex items-center gap-3">
              <Thermometer className="w-5 h-5 text-amber-100" />
              <span className="text-sm text-white/85">{t('login.feature4')}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="col-span-2 p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 shadow-lg rotate-[-2deg] hover:border-emerald-300/50 transition-all">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-emerald-100/70 font-semibold">Rendimiento proyectado</span>
                  <div className="mt-1 text-2xl font-black font-mono">8,240 <span className="text-xs font-semibold text-white/65">kg/ha</span></div>
                </div>
                <div className="p-2 rounded-xl bg-emerald-400/15 border border-emerald-300/25 text-emerald-100">
                  <TrendingUp className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-emerald-100/80">
                <span>+12.8% vs. campaña anterior</span>
                <span className="px-2 py-0.5 rounded-full border border-emerald-300/30 bg-emerald-300/10 font-mono">Óptimo</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 shadow-lg rotate-[1deg] hover:border-teal-300/50 transition-all">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] uppercase tracking-wider text-white/65 font-semibold">Progreso del ciclo</span>
                <span className="text-sm font-black font-mono text-emerald-100">68%</span>
              </div>
              <div className="mt-4 h-2 rounded-full bg-slate-950/40 overflow-hidden">
                <div className="h-full w-[68%] rounded-full bg-gradient-to-r from-emerald-400 to-cyan-300 shadow-[0_0_12px_rgba(16,185,129,0.6)]" />
              </div>
              <div className="mt-2 text-[10px] text-white/60 font-mono">DAP 82 / 120</div>
            </div>

            <div className="p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 shadow-lg rotate-[-1deg] hover:border-amber-300/50 transition-all">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] uppercase tracking-wider text-white/65 font-semibold">CWSI</span>
                <Activity className="w-4 h-4 text-amber-200" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-black font-mono">0.24</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-400/15 text-emerald-100 border border-emerald-300/30 text-[10px] font-semibold">Confort</span>
              </div>
              <div className="mt-2 text-[10px] text-white/60">Estado hídrico estable</div>
            </div>
          </div>
        </div>
      </section>

      <section className="flex-1 min-w-0 relative flex items-center justify-center px-4 py-10 sm:px-8 lg:px-14">
        <div className="absolute top-5 right-5 sm:top-7 sm:right-8 flex items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
            title={theme === 'dark' ? t('app.themeToggleToLight') : t('app.themeToggleToDark')}
            aria-label={theme === 'dark' ? t('app.themeToggleToLight') : t('app.themeToggleToDark')}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>
          <div className="relative">
            <select
              onChange={(event) => {
                const code = event.target.value;
                i18n.changeLanguage(code);
                localStorage.setItem('lang', code);
              }}
              value={i18n.language ?? 'es'}
              className="p-2 pl-8 pr-8 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all cursor-pointer appearance-none text-xs font-bold"
              title={t('app.langSelectorTitle')}
              aria-label={t('app.langSelectorTitle')}
            >
              <option value="es">ES</option>
              <option value="en">EN</option>
              <option value="pt">PT</option>
            </select>
            <Globe className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        <div className="w-full max-w-md pt-12 sm:pt-8">
          <div className="text-center mb-8 md:hidden">
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
      </section>
    </main>
  );
};

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Scale, ShieldAlert } from 'lucide-react';

export const ScientificScopeNotice: React.FC = () => {
  const { t } = useTranslation();

  return (
    <section
      id="scientific-scope-notice"
      aria-labelledby="scientific-scope-title"
      className="rounded-2xl border border-amber-400/50 bg-amber-50/90 p-4 shadow-sm dark:bg-amber-950/20"
    >
      <div className="flex items-start gap-3">
        <div className="rounded-xl border border-amber-400/40 bg-amber-400/15 p-2 text-amber-700 dark:text-amber-300">
          <Scale className="h-5 w-5" aria-hidden="true" />
        </div>
        <div className="min-w-0 space-y-2">
          <div>
            <h2 id="scientific-scope-title" className="flex flex-wrap items-center gap-2 text-sm font-black text-amber-950 dark:text-amber-100">
              {t('scientificScope.title')}
              <span className="rounded-full border border-amber-500/40 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-800 dark:text-amber-200">
                {t('scientificScope.badge')}
              </span>
            </h2>
            <p className="mt-1 max-w-5xl text-xs leading-relaxed text-amber-950/80 dark:text-amber-100/80">
              {t('scientificScope.summary')}
            </p>
          </div>
          <div className="grid gap-1.5 text-[11px] text-slate-700 dark:text-slate-300 md:grid-cols-2">
            <p className="flex items-start gap-1.5"><ShieldAlert className="mt-0.5 h-3.5 w-3.5 flex-none text-rose-500" />{t('scientificScope.limitSpatial')}</p>
            <p className="flex items-start gap-1.5"><ShieldAlert className="mt-0.5 h-3.5 w-3.5 flex-none text-rose-500" />{t('scientificScope.limitSoil')}</p>
            <p className="flex items-start gap-1.5"><ShieldAlert className="mt-0.5 h-3.5 w-3.5 flex-none text-rose-500" />{t('scientificScope.prohibited')}</p>
            <p className="flex items-start gap-1.5"><ShieldAlert className="mt-0.5 h-3.5 w-3.5 flex-none text-cyan-600" />{t('scientificScope.required')}</p>
          </div>
        </div>
      </div>
    </section>
  );
};

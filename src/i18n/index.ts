import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import es from './locales/es.json';
import en from './locales/en.json';
import pt from './locales/pt.json';

const storedLang = typeof window !== 'undefined' ? localStorage.getItem('lang') : null;

void i18n
  .use(initReactI18next)
  .init({
    resources: {
      es: { translation: es },
      en: { translation: en },
      pt: { translation: pt }
    },
    lng: storedLang ?? 'es',
    fallbackLng: 'es',
    supportedLngs: ['es', 'en', 'pt'],
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;

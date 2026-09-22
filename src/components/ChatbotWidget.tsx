import React, { FormEvent, useEffect, useRef, useState } from 'react';
import { Bot, ChevronDown, Loader2, MessageCircle, Send, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { SimulationConfig, SimulationResult } from '../types';
import { sendChatbotMessage, type ChatbotContext } from '../services/api';

type ChatMessage = {
  id: number;
  role: 'assistant' | 'user';
  text: string;
};

interface ChatbotWidgetProps {
  simulationResult?: SimulationResult;
  simulationConfig?: SimulationConfig;
}

const stripMarkdown = (text: string): string =>
  text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/_{1,2}(.*?)_{1,2}/g, '$1')
    .replace(/#{1,6}\s?/g, '')
    .replace(/^-{3,}\s*$/gm, '')
    .replace(/^[\*\-•]\s+/gm, '')
    .replace(/^\d+\.\s+/gm, '')
    .replace(/`{1,3}([^`]*)`{1,3}/g, '$1')
    .replace(/\$\$[\s\S]*?\$\$/g, '')
    .replace(/\$[^\$]*\$/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

export const ChatbotWidget: React.FC<ChatbotWidgetProps> = ({ simulationResult, simulationConfig }) => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 0, role: 'assistant', text: t('chatbot.welcome') }
  ]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending) return;

    const userMessage: ChatMessage = { id: Date.now(), role: 'user', text: trimmedMessage };
    setMessages((current) => [...current, userMessage]);
    setMessage('');
    setIsSending(true);

    try {
      const kpis = simulationResult?.summaryKPIs;
      const context: ChatbotContext = {
        fieldName: simulationResult?.fieldName,
        fieldLocation: simulationResult?.fieldLocation,
        scenario: simulationConfig?.scenario,
        targetYear: simulationConfig?.targetYear,
        inferenceMode: simulationResult?.inferenceMode,
        modelName: simulationResult?.modelName,
        modelDataSource: simulationResult?.modelDataSource,
        projectedYieldKgHa: kpis?.projectedYieldKgHa,
        yieldLossDueToDroughtPercent: kpis?.yieldLossDueToDroughtPercent,
        totalWaterConsumedMm: kpis?.totalWaterConsumedMm,
        peakWaterStressIndex: kpis?.peakWaterStressIndex,
        droughtResilienceScore: kpis?.droughtResilienceScore,
      };
      const reply = await sendChatbotMessage(trimmedMessage, context);
      setMessages((current) => [
        ...current,
        { id: Date.now() + 1, role: 'assistant', text: reply }
      ]);
    } catch (error) {
      console.error('Chatbot request failed', error);
      setMessages((current) => [
        ...current,
        { id: Date.now() + 1, role: 'assistant', text: t('chatbot.error') }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-[60] flex flex-col items-end gap-3 sm:bottom-6 sm:right-6">
      {isOpen && (
        <section className="flex h-[600px] max-h-[calc(100vh-8rem)] w-[380px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-slate-950/20 dark:border-slate-700 dark:bg-slate-900 dark:shadow-black/40">
          <header className="flex shrink-0 items-center justify-between bg-gradient-to-r from-emerald-600 to-teal-500 px-4 py-3 text-white">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              <div>
                <h2 className="text-sm font-bold">{t('chatbot.title')}</h2>
                <p className="text-[11px] text-emerald-50/85">{t('chatbot.subtitle')}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="rounded-lg p-1.5 text-white/80 transition hover:bg-white/15 hover:text-white"
              aria-label={t('chatbot.close')}
              title={t('chatbot.close')}
            >
              <X className="h-4 w-4" />
            </button>
          </header>

          <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto bg-slate-50 p-4 dark:bg-slate-950/80" aria-live="polite">
            {messages.map((chatMessage) => (
              <div
                key={chatMessage.id}
                className={`max-w-[88%] rounded-2xl px-3 py-2 text-sm leading-5 ${
                  chatMessage.role === 'user'
                    ? 'self-end rounded-br-md bg-emerald-600 text-white'
                    : 'self-start rounded-bl-md border border-slate-200 bg-white text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200'
                }`}
              >
                {chatMessage.role === 'assistant' ? stripMarkdown(chatMessage.text) : chatMessage.text}
              </div>
            ))}
            {isSending && (
              <div className="w-fit max-w-[88%] self-start rounded-2xl rounded-bl-md border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                <Loader2 className="h-4 w-4 animate-spin text-emerald-500" aria-label={t('chatbot.loading')} />
              </div>
            )}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>

          <form onSubmit={handleSubmit} className="flex shrink-0 gap-2 border-t border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <input
              type="text"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder={t('chatbot.placeholder')}
              aria-label={t('chatbot.placeholder')}
              disabled={isSending}
              className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
            <button
              type="submit"
              disabled={isSending || !message.trim()}
              className="rounded-xl bg-emerald-600 px-3 text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label={t('chatbot.send')}
              title={t('chatbot.send')}
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-600 text-white shadow-xl shadow-emerald-700/30 transition hover:scale-105 hover:bg-emerald-500"
        aria-label={isOpen ? t('chatbot.close') : t('chatbot.open')}
        title={isOpen ? t('chatbot.close') : t('chatbot.open')}
      >
        {isOpen ? <ChevronDown className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>
    </div>
  );
};

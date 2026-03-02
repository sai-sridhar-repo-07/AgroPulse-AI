/**
 * AgroPulse AI - Generative AI Explanation Panel (Beautiful Redesign)
 */
import React, { useState } from 'react';
import { Brain, ChevronDown, ChevronUp, Shield, Lightbulb, Sparkles, CheckCircle2 } from 'lucide-react';
import { ExplanationResponse } from '../../types';

interface Props {
  data: ExplanationResponse;
  isLoading?: boolean;
}

const ExplanationPanel: React.FC<Props> = ({ data, isLoading }) => {
  const [expanded, setExpanded] = useState(true);

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-card p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
            <Brain className="w-5 h-5 text-purple-600 animate-pulse" />
          </div>
          <div>
            <h3 className="font-bold text-gray-800">AI is Thinking...</h3>
            <p className="text-xs text-gray-400">Amazon Bedrock is generating your insights</p>
          </div>
        </div>
        <div className="space-y-3">
          {[90, 75, 85, 60].map((w, i) => (
            <div key={i} className="h-3 bg-gray-100 rounded-full animate-shimmer" style={{ width: `${w}%` }} />
          ))}
        </div>
      </div>
    );
  }

  const modelLabel = data.model_used?.includes('claude') ? 'Claude AI' :
                     data.model_used?.includes('titan') ? 'Amazon Titan' :
                     data.model_used || 'AI Model';

  return (
    <div className="bg-white rounded-2xl shadow-card overflow-hidden">
      {/* Purple Gradient Header */}
      <div className="relative bg-gradient-to-br from-violet-700 via-purple-600 to-indigo-600 p-5 overflow-hidden">
        <div className="absolute -top-6 -right-6 w-32 h-32 bg-white/10 rounded-full" />
        <div className="absolute -bottom-8 right-12 w-20 h-20 bg-white/5 rounded-full" />
        <div className="relative flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5 mb-0.5">
                <Sparkles className="w-3.5 h-3.5 text-purple-200" />
                <span className="text-purple-200 text-xs font-semibold uppercase tracking-widest">
                  AI Explanation
                </span>
              </div>
              <h3 className="text-white font-bold text-base leading-tight">
                Personalized Farm Insights
              </h3>
              <p className="text-purple-200 text-xs mt-0.5">
                {modelLabel} · Amazon Bedrock
                {data.tokens_used && ` · ${data.tokens_used} tokens`}
              </p>
            </div>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 text-purple-200 hover:text-white hover:bg-white/20 rounded-lg transition-all flex-shrink-0"
          >
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="p-5 space-y-5">
          {/* Main Explanation */}
          <div className="relative bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-100 rounded-2xl p-4">
            <div className="absolute top-3 right-3">
              <Sparkles className="w-4 h-4 text-purple-300" />
            </div>
            <p className="text-sm text-gray-700 leading-relaxed pr-6">{data.explanation}</p>
          </div>

          {/* Confidence Narrative */}
          {data.confidence_narrative && (
            <div className="flex gap-3 bg-gray-50 border border-gray-100 rounded-xl p-3.5">
              <div className="w-5 h-5 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-3 h-3 text-purple-500" />
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">{data.confidence_narrative}</p>
            </div>
          )}

          {/* Key Insights + Action Steps in 2-col on wider screens */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Key Insights */}
            {data.key_insights && data.key_insights.length > 0 && (
              <div className="bg-amber-50 border border-amber-100 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center">
                    <Lightbulb className="w-3.5 h-3.5 text-amber-600" />
                  </div>
                  <h4 className="text-sm font-bold text-gray-800">Key Insights</h4>
                </div>
                <ul className="space-y-2.5">
                  {data.key_insights.map((insight, i) => (
                    <li key={i} className="flex gap-2.5 text-xs text-gray-700">
                      <div className="w-4 h-4 bg-amber-200 text-amber-800 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold mt-0.5">
                        {i + 1}
                      </div>
                      <span className="leading-relaxed">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Steps */}
            {data.risk_mitigation && data.risk_mitigation.length > 0 && (
              <div className="bg-agro-green-50 border border-agro-green-100 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-7 h-7 bg-agro-green-100 rounded-lg flex items-center justify-center">
                    <Shield className="w-3.5 h-3.5 text-agro-green-600" />
                  </div>
                  <h4 className="text-sm font-bold text-gray-800">Action Steps</h4>
                </div>
                <ul className="space-y-2.5">
                  {data.risk_mitigation.map((step, i) => (
                    <li key={i} className="flex gap-2.5 text-xs text-gray-700">
                      <CheckCircle2 className="w-4 h-4 text-agro-green-500 flex-shrink-0 mt-0.5" />
                      <span className="leading-relaxed">{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 bg-agro-green-400 rounded-full animate-pulse-slow" />
              <span className="text-xs text-gray-400">
                Language: <span className="font-medium text-gray-600">{data.language?.toUpperCase()}</span>
              </span>
            </div>
            <span className="text-xs text-gray-400">
              Generated {new Date(data.generated_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplanationPanel;

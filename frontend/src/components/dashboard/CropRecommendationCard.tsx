/**
 * AgroPulse AI - Crop Recommendation Card (Beautiful Redesign)
 */
import React from 'react';
import { Sprout, TrendingUp, Droplets, Clock, Award } from 'lucide-react';
import { CropRecommendationResponse } from '../../types';

interface Props {
  data: CropRecommendationResponse;
}

const CROP_EMOJI: Record<string, string> = {
  rice: '🌾', wheat: '🌿', maize: '🌽', cotton: '🌱', sugarcane: '🎋',
  chickpea: '🫘', lentil: '🫛', soybean: '🫘', groundnut: '🥜',
  coffee: '☕', coconut: '🥥', banana: '🍌', mango: '🥭',
  apple: '🍎', grapes: '🍇', papaya: '🍈', orange: '🍊', default: '🌱',
};

const AnimatedBar: React.FC<{ value: number; color?: string; delay?: number }> = ({
  value,
  color = 'bg-agro-green-500',
  delay = 0,
}) => (
  <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
    <div
      className={`${color} h-2 rounded-full transition-all duration-1000 ease-out`}
      style={{
        width: `${value * 100}%`,
        transitionDelay: `${delay}ms`,
      }}
    />
  </div>
);

const CropRecommendationCard: React.FC<Props> = ({ data }) => {
  const [top, ...rest] = data.recommendations;

  return (
    <div className="bg-white rounded-2xl shadow-card overflow-hidden card-hover h-full">
      {/* Gradient Header */}
      <div className="relative bg-gradient-to-br from-agro-green-700 via-agro-green-600 to-agro-green-500 p-5 overflow-hidden">
        {/* Decorative circle */}
        <div className="absolute -top-6 -right-6 w-28 h-28 bg-white/10 rounded-full" />
        <div className="absolute -bottom-8 -right-2 w-20 h-20 bg-white/5 rounded-full" />
        <div className="relative flex items-start justify-between">
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <Sprout className="w-4 h-4 text-agro-green-200" />
              <span className="text-agro-green-200 text-xs font-semibold uppercase tracking-widest">
                Crop Recommendation
              </span>
            </div>
            <h3 className="text-white font-bold text-lg leading-tight">
              Best Crop for Your Farm
            </h3>
            <p className="text-agro-green-200 text-xs mt-1">
              {data.location} · {data.model_version}
            </p>
          </div>
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <Award className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Top Recommendation Hero */}
        {top && (
          <div className="flex items-center gap-4 p-4 bg-gradient-to-r from-agro-green-50 to-emerald-50 rounded-2xl border border-agro-green-100">
            <div className="text-5xl animate-float flex-shrink-0">
              {CROP_EMOJI[top.crop_name.toLowerCase()] || CROP_EMOJI.default}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-xl font-extrabold text-gray-900 capitalize tracking-tight">
                  {top.crop_name}
                </h4>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-agro-green-500 text-white shadow-sm">
                  #1 Pick
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-2">
                AI Confidence Score
              </p>
              <AnimatedBar value={top.confidence_score} color="bg-agro-green-500" delay={300} />
              <div className="flex justify-between mt-1">
                <span className="text-xs text-gray-400">0%</span>
                <span className="text-xs font-bold text-agro-green-700">
                  {(top.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Crop Metadata Grid */}
        {top && (top.growing_season_days || top.water_requirement_mm || top.expected_yield_kg_per_hectare) && (
          <div className="grid grid-cols-3 gap-2">
            {top.expected_yield_kg_per_hectare && (
              <div className="bg-agro-green-50 rounded-xl p-3 text-center border border-agro-green-100">
                <TrendingUp className="w-4 h-4 text-agro-green-600 mx-auto mb-1.5" />
                <div className="text-sm font-bold text-gray-800 leading-none">
                  {top.expected_yield_kg_per_hectare.toLocaleString()}
                </div>
                <div className="text-[10px] text-gray-500 mt-0.5">kg/ha yield</div>
              </div>
            )}
            {top.growing_season_days && (
              <div className="bg-blue-50 rounded-xl p-3 text-center border border-blue-100">
                <Clock className="w-4 h-4 text-blue-600 mx-auto mb-1.5" />
                <div className="text-sm font-bold text-gray-800 leading-none">
                  {top.growing_season_days}
                </div>
                <div className="text-[10px] text-gray-500 mt-0.5">days season</div>
              </div>
            )}
            {top.water_requirement_mm && (
              <div className="bg-sky-50 rounded-xl p-3 text-center border border-sky-100">
                <Droplets className="w-4 h-4 text-sky-500 mx-auto mb-1.5" />
                <div className="text-sm font-bold text-gray-800 leading-none">
                  {top.water_requirement_mm}
                </div>
                <div className="text-[10px] text-gray-500 mt-0.5">mm water</div>
              </div>
            )}
          </div>
        )}

        {/* Alternative Crops */}
        {rest.length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
              Alternatives
            </p>
            <div className="space-y-3">
              {rest.map((crop, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <span className="text-xl flex-shrink-0">
                    {CROP_EMOJI[crop.crop_name.toLowerCase()] || CROP_EMOJI.default}
                  </span>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium capitalize text-gray-700">
                        {crop.crop_name}
                      </span>
                      <span className="text-xs font-bold text-gray-500 tabular-nums">
                        {(crop.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <AnimatedBar
                      value={crop.confidence_score}
                      color={idx === 0 ? 'bg-agro-earth-400' : 'bg-gray-300'}
                      delay={400 + idx * 100}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Feature Importance Chips */}
        {data.feature_importance && Object.keys(data.feature_importance).length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2.5">
              Key Decision Factors
            </p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(data.feature_importance)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([key, val]) => (
                  <span
                    key={key}
                    className="inline-flex items-center px-2.5 py-1 rounded-lg bg-gray-100 text-xs font-medium text-gray-600 hover:bg-agro-green-100 hover:text-agro-green-800 transition-colors cursor-default"
                  >
                    {key.charAt(0).toUpperCase() + key.slice(1)}: {(val * 100).toFixed(0)}%
                  </span>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CropRecommendationCard;

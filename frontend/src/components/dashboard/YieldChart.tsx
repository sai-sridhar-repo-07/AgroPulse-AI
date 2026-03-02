/**
 * AgroPulse AI - Yield Prediction Chart (Beautiful Redesign)
 */
import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend, ChartOptions,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { TrendingUp, Target, Layers, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { YieldPredictionResponse } from '../../types';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface Props {
  data: YieldPredictionResponse;
}

const IMPACT_COLOR: Record<string, string> = {
  High: 'text-agro-green-600 bg-agro-green-50',
  Medium: 'text-agro-earth-600 bg-agro-earth-50',
  Low: 'text-gray-500 bg-gray-100',
};

const YieldChart: React.FC<Props> = ({ data }) => {
  const chartData = {
    labels: ['Low Est.', 'Predicted', 'High Est.'],
    datasets: [
      {
        label: 'Yield (kg/ha)',
        data: [
          data.confidence_interval_lower,
          data.predicted_yield_kg_per_hectare,
          data.confidence_interval_upper,
        ],
        backgroundColor: [
          'rgba(251,191,36,0.25)',
          'rgba(34,197,94,0.85)',
          'rgba(14,165,233,0.25)',
        ],
        borderColor: [
          'rgba(251,191,36,0.8)',
          'rgba(34,197,94,1)',
          'rgba(14,165,233,0.8)',
        ],
        borderWidth: 2,
        borderRadius: 10,
        borderSkipped: false,
      },
    ],
  };

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(17,24,39,0.9)',
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: (ctx) => ` ${(ctx.parsed.y ?? 0).toLocaleString()} kg/ha`,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: (val) => `${(Number(val) / 1000).toFixed(1)}k`,
          color: '#9ca3af',
          font: { size: 11 },
        },
        grid: { color: 'rgba(0,0,0,0.04)' },
        border: { display: false },
      },
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: { color: '#6b7280', font: { size: 11 } },
      },
    },
  };

  const rangeSpread = data.confidence_interval_upper - data.confidence_interval_lower;
  const rangePercent = ((rangeSpread / data.predicted_yield_kg_per_hectare) * 100).toFixed(0);

  return (
    <div className="bg-white rounded-2xl shadow-card overflow-hidden card-hover h-full">
      {/* Gradient Header */}
      <div className="relative bg-gradient-to-br from-blue-700 via-blue-600 to-sky-500 p-5 overflow-hidden">
        <div className="absolute -top-6 -right-6 w-28 h-28 bg-white/10 rounded-full" />
        <div className="absolute -bottom-8 -right-2 w-20 h-20 bg-white/5 rounded-full" />
        <div className="relative flex items-start justify-between">
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <TrendingUp className="w-4 h-4 text-blue-200" />
              <span className="text-blue-200 text-xs font-semibold uppercase tracking-widest">
                Yield Prediction
              </span>
            </div>
            <h3 className="text-white font-bold text-lg leading-tight capitalize">
              {data.crop} Harvest Forecast
            </h3>
            <p className="text-blue-200 text-xs mt-1">
              {data.model_version} · Gradient Boost
            </p>
          </div>
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <Layers className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Key Metrics Row */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-agro-green-50 border border-agro-green-100 rounded-2xl p-4">
            <div className="flex items-center gap-1.5 mb-2">
              <Target className="w-3.5 h-3.5 text-agro-green-600" />
              <span className="text-xs text-gray-500 font-medium">Per Hectare</span>
            </div>
            <div className="text-2xl font-extrabold text-gray-900 leading-none tabular-nums">
              {data.predicted_yield_kg_per_hectare.toLocaleString()}
            </div>
            <div className="text-xs text-agro-green-700 font-medium mt-0.5">kg/ha</div>
          </div>
          <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4">
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
              <span className="text-xs text-gray-500 font-medium">Total Harvest</span>
            </div>
            <div className="text-2xl font-extrabold text-gray-900 leading-none tabular-nums">
              {(data.total_yield_kg / 1000).toFixed(1)}
            </div>
            <div className="text-xs text-blue-700 font-medium mt-0.5">metric tonnes</div>
          </div>
        </div>

        {/* Confidence Range Banner */}
        <div className="flex items-center justify-between bg-gray-50 border border-gray-100 rounded-xl px-4 py-3">
          <div className="flex items-center gap-2">
            <ArrowDownRight className="w-4 h-4 text-amber-500" />
            <div>
              <div className="text-xs text-gray-400">Low Estimate</div>
              <div className="text-sm font-bold text-gray-700">{data.confidence_interval_lower.toLocaleString()}</div>
            </div>
          </div>
          <div className="text-center">
            <div className="text-[10px] text-gray-400 uppercase tracking-wider">Confidence Range</div>
            <div className="text-xs font-bold text-gray-600">±{rangePercent}%</div>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-right">
              <div className="text-xs text-gray-400">High Estimate</div>
              <div className="text-sm font-bold text-gray-700">{data.confidence_interval_upper.toLocaleString()}</div>
            </div>
            <ArrowUpRight className="w-4 h-4 text-sky-500" />
          </div>
        </div>

        {/* Bar Chart */}
        <div className="h-36">
          <Bar data={chartData} options={options} />
        </div>

        {/* Key Factors */}
        {data.key_factors && data.key_factors.length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2.5">
              Top Influencing Factors
            </p>
            <div className="flex flex-wrap gap-2">
              {data.key_factors.slice(0, 3).map((f, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium ${IMPACT_COLOR[f.impact] || 'text-gray-500 bg-gray-100'}`}
                >
                  <span>{f.factor}</span>
                  <span className="opacity-70">·</span>
                  <span>{f.impact}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default YieldChart;

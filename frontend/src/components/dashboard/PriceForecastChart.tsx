/**
 * AgroPulse AI - Price Forecast Chart (Beautiful Redesign)
 */
import React from 'react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Filler, Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { TrendingUp, TrendingDown, Minus, IndianRupee, BarChart2 } from 'lucide-react';
import { PriceForecastResponse } from '../../types';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Filler, Legend
);

interface Props {
  data: PriceForecastResponse;
}

const SIGNAL_CONFIG = {
  'SELL NOW': {
    gradient: 'from-red-600 to-rose-500',
    bg: 'bg-red-50 border-red-200',
    text: 'text-red-700',
    dot: 'bg-red-500',
    icon: TrendingDown,
    label: 'Sell Now',
    desc: 'Prices expected to decline. Consider selling immediately.',
  },
  'SELL': {
    gradient: 'from-agro-earth-600 to-amber-500',
    bg: 'bg-amber-50 border-amber-200',
    text: 'text-amber-700',
    dot: 'bg-amber-500',
    icon: TrendingUp,
    label: 'Sell',
    desc: 'Favorable conditions. A good time to sell your produce.',
  },
  'HOLD': {
    gradient: 'from-blue-600 to-sky-500',
    bg: 'bg-blue-50 border-blue-200',
    text: 'text-blue-700',
    dot: 'bg-blue-500',
    icon: Minus,
    label: 'Hold',
    desc: 'Market is stable. Consider holding for a better price.',
  },
  'BUY': {
    gradient: 'from-agro-green-600 to-emerald-500',
    bg: 'bg-agro-green-50 border-agro-green-200',
    text: 'text-agro-green-700',
    dot: 'bg-agro-green-500',
    icon: TrendingUp,
    label: 'Buy',
    desc: 'Prices are low. Good time to procure inputs.',
  },
};

const PriceForecastChart: React.FC<Props> = ({ data }) => {
  const labels = data.forecast.slice(0, 14).map(p =>
    new Date(p.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  );
  const prices = data.forecast.slice(0, 14).map(p => p.predicted_price);
  const upper = data.forecast.slice(0, 14).map(p => p.upper_bound);
  const lower = data.forecast.slice(0, 14).map(p => p.lower_bound);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Upper Bound',
        data: upper,
        borderColor: 'transparent',
        backgroundColor: 'rgba(34,197,94,0.08)',
        fill: '+1',
        tension: 0.4,
        pointRadius: 0,
      },
      {
        label: `${data.commodity} Price`,
        data: prices,
        borderColor: 'rgba(34,197,94,1)',
        backgroundColor: 'rgba(34,197,94,0.05)',
        fill: true,
        tension: 0.4,
        borderWidth: 2.5,
        pointBackgroundColor: 'rgba(34,197,94,1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 7,
      },
      {
        label: 'Lower Bound',
        data: lower,
        borderColor: 'transparent',
        backgroundColor: 'rgba(34,197,94,0.08)',
        fill: '-1',
        tension: 0.4,
        pointRadius: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: 'index' as const },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(17,24,39,0.92)',
        padding: 12,
        cornerRadius: 10,
        callbacks: {
          label: (ctx: any) =>
            ctx.dataset.label === `${data.commodity} Price`
              ? ` ₹${ctx.parsed.y.toLocaleString('en-IN')}/Quintal`
              : '',
          title: (items: any[]) => `📅 ${items[0].label}`,
        },
        filter: (item: any) => item.dataset.label === `${data.commodity} Price`,
      },
    },
    scales: {
      y: {
        ticks: {
          callback: (val: any) => `₹${Number(val).toLocaleString('en-IN')}`,
          color: '#9ca3af',
          font: { size: 11 },
        },
        grid: { color: 'rgba(0,0,0,0.04)' },
        border: { display: false },
      },
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: {
          maxRotation: 0,
          font: { size: 10 },
          color: '#9ca3af',
          maxTicksLimit: 7,
        },
      },
    },
  };

  const signal = data.market_signal as keyof typeof SIGNAL_CONFIG;
  const signalCfg = SIGNAL_CONFIG[signal] || SIGNAL_CONFIG['HOLD'];
  const SignalIcon = signalCfg.icon;

  const forecastEnd = data.forecast[data.forecast.length - 1]?.predicted_price || data.current_price;
  const priceChange = forecastEnd - data.current_price;
  const priceChangePercent = ((priceChange / data.current_price) * 100).toFixed(1);

  return (
    <div className="bg-white rounded-2xl shadow-card overflow-hidden card-hover">
      {/* Gradient Header */}
      <div className="relative bg-gradient-to-br from-agro-earth-700 via-agro-earth-600 to-amber-500 p-5 overflow-hidden">
        <div className="absolute -top-6 -right-6 w-32 h-32 bg-white/10 rounded-full" />
        <div className="absolute -bottom-10 -right-2 w-24 h-24 bg-white/5 rounded-full" />
        <div className="relative flex items-start justify-between">
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <IndianRupee className="w-4 h-4 text-agro-earth-200" />
              <span className="text-agro-earth-200 text-xs font-semibold uppercase tracking-widest">
                Market Price Forecast
              </span>
            </div>
            <h3 className="text-white font-bold text-lg leading-tight">
              {data.commodity} · {data.state}
            </h3>
            <p className="text-agro-earth-200 text-xs mt-1">
              14-day AI Price Prediction
            </p>
          </div>
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <BarChart2 className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Price + Signal Row */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          {/* Current Price */}
          <div className="flex-1">
            <p className="text-xs text-gray-400 font-medium mb-1">Current Market Price</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-gray-900 tabular-nums">
                ₹{data.current_price.toLocaleString('en-IN')}
              </span>
              <span className="text-sm text-gray-400">/{data.unit.split('/')[1] || 'Quintal'}</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              {priceChange >= 0 ? (
                <TrendingUp className="w-3.5 h-3.5 text-agro-green-500" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5 text-red-500" />
              )}
              <span className={`text-xs font-semibold ${priceChange >= 0 ? 'text-agro-green-600' : 'text-red-600'}`}>
                {priceChange >= 0 ? '+' : ''}{priceChangePercent}% in 14 days
              </span>
            </div>
          </div>

          {/* Market Signal Badge */}
          <div className={`flex items-center gap-3 px-4 py-3 rounded-2xl border ${signalCfg.bg} flex-shrink-0`}>
            <div className={`w-8 h-8 rounded-xl bg-gradient-to-br ${signalCfg.gradient} flex items-center justify-center shadow-sm`}>
              <SignalIcon className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className={`text-sm font-extrabold tracking-tight ${signalCfg.text}`}>
                {signalCfg.label}
              </div>
              <div className="text-[10px] text-gray-500 font-medium">Market Signal</div>
            </div>
          </div>
        </div>

        {/* Signal Advice */}
        <div className={`flex items-start gap-2.5 p-3 rounded-xl border ${signalCfg.bg}`}>
          <div className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${signalCfg.dot} animate-pulse-slow`} />
          <p className={`text-xs leading-relaxed font-medium ${signalCfg.text}`}>
            {signalCfg.desc}
          </p>
        </div>

        {/* Price Chart */}
        <div className="h-48">
          <Line data={chartData} options={options as any} />
        </div>

        {/* Trend Footer */}
        <div className="flex items-center justify-between text-xs text-gray-400 pt-1 border-t border-gray-100">
          <span className="capitalize">
            Trend: <span className="font-semibold text-agro-green-700">{data.price_trend}</span>
          </span>
          <span>
            14-day forecast · {data.unit}
          </span>
        </div>
      </div>
    </div>
  );
};

export default PriceForecastChart;

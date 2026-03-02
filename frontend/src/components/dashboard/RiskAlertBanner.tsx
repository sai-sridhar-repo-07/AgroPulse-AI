/**
 * AgroPulse AI - Risk Alert Banner (Beautiful Redesign)
 */
import React from 'react';
import { AlertTriangle, CloudRain, TrendingDown, Bug, X, CheckCircle, Shield } from 'lucide-react';
import { Alert } from '../../types';

interface Props {
  alerts: Alert[];
  onDismiss?: (id: string) => void;
}

const SEVERITY_CONFIG = {
  critical: {
    wrapperBg: 'bg-red-50 border-red-200',
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    badge: 'bg-red-500 text-white',
    badgeLabel: 'Critical',
    dot: 'bg-red-500',
    titleColor: 'text-red-900',
    msgColor: 'text-red-700',
    metaColor: 'text-red-400',
  },
  high: {
    wrapperBg: 'bg-orange-50 border-orange-200',
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-600',
    badge: 'bg-orange-500 text-white',
    badgeLabel: 'High Risk',
    dot: 'bg-orange-500',
    titleColor: 'text-orange-900',
    msgColor: 'text-orange-700',
    metaColor: 'text-orange-400',
  },
  medium: {
    wrapperBg: 'bg-yellow-50 border-yellow-200',
    iconBg: 'bg-yellow-100',
    iconColor: 'text-yellow-600',
    badge: 'bg-yellow-400 text-yellow-900',
    badgeLabel: 'Medium',
    dot: 'bg-yellow-500',
    titleColor: 'text-yellow-900',
    msgColor: 'text-yellow-800',
    metaColor: 'text-yellow-500',
  },
  low: {
    wrapperBg: 'bg-blue-50 border-blue-200',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    badge: 'bg-blue-100 text-blue-700',
    badgeLabel: 'Low Risk',
    dot: 'bg-blue-400',
    titleColor: 'text-blue-900',
    msgColor: 'text-blue-700',
    metaColor: 'text-blue-400',
  },
};

const ALERT_ICONS: Record<string, React.FC<{ className?: string }>> = {
  weather: CloudRain,
  market: TrendingDown,
  pest: Bug,
  default: AlertTriangle,
};

const RiskAlertBanner: React.FC<Props> = ({ alerts, onDismiss }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-agro-green-50 border border-agro-green-200 rounded-2xl p-4 flex items-center gap-4 shadow-sm">
        <div className="w-10 h-10 bg-agro-green-100 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm">
          <CheckCircle className="w-5 h-5 text-agro-green-600" />
        </div>
        <div>
          <p className="text-sm font-bold text-agro-green-800">All Clear — No Active Alerts</p>
          <p className="text-xs text-agro-green-600 mt-0.5">
            Your farm area has no weather, pest, or market alerts at this time.
          </p>
        </div>
        <Shield className="w-6 h-6 text-agro-green-300 ml-auto flex-shrink-0" />
      </div>
    );
  }

  const unread = alerts.filter(a => !a.is_read).length;

  return (
    <div className="space-y-3">
      {/* Header Row */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          <span className="text-sm font-bold text-gray-800">Active Alerts</span>
        </div>
        {unread > 0 && (
          <span className="bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full animate-pulse-slow">
            {unread} new
          </span>
        )}
      </div>

      {/* Alert Cards */}
      {alerts.map((alert) => {
        const cfg = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.low;
        const Icon = ALERT_ICONS[alert.alert_type] || ALERT_ICONS.default;

        return (
          <div
            key={alert.id}
            className={`border rounded-2xl p-4 ${cfg.wrapperBg} transition-all duration-300 animate-fade-in-up`}
          >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${cfg.iconBg}`}>
                <Icon className={`w-4 h-4 ${cfg.iconColor}`} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start gap-2 justify-between mb-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className={`text-sm font-bold ${cfg.titleColor} leading-tight`}>
                      {alert.title}
                    </h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${cfg.badge}`}>
                      {cfg.badgeLabel}
                    </span>
                    {!alert.is_read && (
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot} animate-pulse`} />
                    )}
                  </div>
                  {onDismiss && (
                    <button
                      onClick={() => onDismiss(alert.id)}
                      className={`${cfg.iconColor} hover:opacity-70 transition-opacity flex-shrink-0 ml-1`}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <p className={`text-xs leading-relaxed ${cfg.msgColor}`}>
                  {alert.message}
                </p>

                <div className="flex items-center justify-between mt-2.5">
                  <div className="flex items-center gap-1.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                    <span className={`text-[10px] font-medium ${cfg.metaColor}`}>
                      Risk Score: {(alert.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <span className={`text-[10px] ${cfg.metaColor}`}>
                    {new Date(alert.created_at).toLocaleDateString('en-IN', {
                      day: 'numeric', month: 'short'
                    })}
                  </span>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RiskAlertBanner;

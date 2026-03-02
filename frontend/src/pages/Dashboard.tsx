/**
 * AgroPulse AI - Main Dashboard (Beautiful Grid Layout)
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Leaf, LogOut, RefreshCw, Bell, ArrowLeft, MapPin, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { authAPI, alertsAPI } from '../services/api';
import CropRecommendationCard from '../components/dashboard/CropRecommendationCard';
import YieldChart from '../components/dashboard/YieldChart';
import PriceForecastChart from '../components/dashboard/PriceForecastChart';
import RiskAlertBanner from '../components/dashboard/RiskAlertBanner';
import ExplanationPanel from '../components/dashboard/ExplanationPanel';
import {
  CropRecommendationResponse,
  YieldPredictionResponse,
  PriceForecastResponse,
  ExplanationResponse,
  Alert,
} from '../types';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [cropData, setCropData] = useState<CropRecommendationResponse | null>(null);
  const [yieldData, setYieldData] = useState<YieldPredictionResponse | null>(null);
  const [priceData, setPriceData] = useState<PriceForecastResponse | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [farmerName, setFarmerName] = useState('Farmer');
  const [location, setLocation] = useState('');

  useEffect(() => {
    const crop = sessionStorage.getItem('crop_result');
    const yieldR = sessionStorage.getItem('yield_result');
    const price = sessionStorage.getItem('price_result');
    const exp = sessionStorage.getItem('explanation');
    const farmer = sessionStorage.getItem('farmer_data');

    if (crop) setCropData(JSON.parse(crop));
    if (yieldR) setYieldData(JSON.parse(yieldR));
    if (price) setPriceData(JSON.parse(price));
    if (exp) setExplanation(JSON.parse(exp));
    if (farmer) {
      const fd = JSON.parse(farmer);
      setFarmerName(fd.name || 'Farmer');
      if (fd.district && fd.state) setLocation(`${fd.district}, ${fd.state}`);
    }

    if (!crop) loadDemoData();

    alertsAPI.getAlerts('demo-farmer-001')
      .then(res => setAlerts(res.alerts))
      .catch(() => {});
  }, []);

  const loadDemoData = () => {
    const demoFarmer = localStorage.getItem('farmer_name') || 'Demo Farmer';
    setFarmerName(demoFarmer);
    setLocation('Pune, Maharashtra');

    const demoCrop: CropRecommendationResponse = {
      recommendations: [
        { crop_name: 'rice', confidence_score: 0.87, expected_yield_kg_per_hectare: 4500, growing_season_days: 120, water_requirement_mm: 1200 },
        { crop_name: 'wheat', confidence_score: 0.61, expected_yield_kg_per_hectare: 3800, growing_season_days: 100, water_requirement_mm: 450 },
        { crop_name: 'maize', confidence_score: 0.45, expected_yield_kg_per_hectare: 5200, growing_season_days: 90, water_requirement_mm: 600 },
      ],
      top_crop: 'rice', confidence: 0.87, model_version: 'xgboost-v1',
      feature_importance: { nitrogen: 0.30, rainfall: 0.25, temperature: 0.20, ph: 0.15, phosphorus: 0.05, potassium: 0.05 },
      prediction_id: 'demo-001', location: 'Pune, Maharashtra',
      generated_at: new Date().toISOString(),
    };

    const demoYield: YieldPredictionResponse = {
      crop: 'rice', predicted_yield_kg_per_hectare: 4350, total_yield_kg: 10875,
      confidence_interval_lower: 3697, confidence_interval_upper: 5002,
      key_factors: [
        { factor: 'Nitrogen', impact: 'High', value: 90 },
        { factor: 'Irrigation', impact: 'Medium', value: true },
        { factor: 'Temperature', impact: 'Medium', value: 25 },
      ],
      prediction_id: 'demo-002', model_version: 'gradient-boost-v1',
      generated_at: new Date().toISOString(),
    };

    const demoPrice: PriceForecastResponse = {
      commodity: 'Rice', state: 'Maharashtra', current_price: 2183, unit: 'INR/Quintal',
      forecast: Array.from({ length: 14 }, (_, i) => {
        const d = new Date(); d.setDate(d.getDate() + i + 1);
        const p = 2183 * (1 + i * 0.003 + Math.sin(i) * 0.01);
        return {
          date: d.toISOString().split('T')[0],
          predicted_price: Math.round(p),
          lower_bound: Math.round(p * 0.96),
          upper_bound: Math.round(p * 1.04),
          trend: 'rising',
        };
      }),
      price_trend: 'rising', market_signal: 'SELL',
      prediction_id: 'demo-003', generated_at: new Date().toISOString(),
    };

    const demoExplanation: ExplanationResponse = {
      explanation: "Based on your soil's high nitrogen content (90 kg/ha), adequate rainfall of 800mm, and suitable temperature of 25°C in Pune district, our AI model strongly recommends Rice cultivation this Kharif season. The soil pH of 6.5 is ideal for rice, and the confidence level of 87% indicates highly favorable conditions.",
      key_insights: [
        "High soil nitrogen (90 kg/ha) perfectly supports rice's nutrient requirements",
        "Rainfall of 800mm exceeds rice's minimum water needs of 750mm",
        "Temperature range of 20-35°C in your region is optimal for rice growth",
      ],
      risk_mitigation: [
        "Prepare nursery beds by May-June for Kharif sowing season",
        "Ensure drainage channels are clear before heavy monsoon rains",
        "Apply Zinc Sulphate (25 kg/ha) to address potential micronutrient deficiency",
      ],
      confidence_narrative: "The 87% confidence score means our AI has high certainty in this recommendation, driven primarily by your soil nitrogen levels and historical rainfall data for your district.",
      language: 'en', tokens_used: 342,
      model_used: 'anthropic.claude-3-sonnet-20240229-v1:0',
      generated_at: new Date().toISOString(),
    };

    const demoAlerts: Alert[] = [
      {
        id: '1', alert_type: 'weather', severity: 'medium',
        title: 'Heavy Rainfall Expected',
        message: 'Moderate to heavy rainfall (45-65mm) expected in Pune district in the next 72 hours. Ensure proper field drainage.',
        risk_score: 0.58, is_read: false, created_at: new Date().toISOString(),
      },
    ];

    setCropData(demoCrop);
    setYieldData(demoYield);
    setPriceData(demoPrice);
    setExplanation(demoExplanation);
    setAlerts(demoAlerts);
  };

  const handleLogout = () => {
    authAPI.logout();
    sessionStorage.clear();
    navigate('/login');
  };

  const unreadCount = alerts.filter(a => !a.is_read).length;

  return (
    <div className="min-h-screen gradient-page">
      {/* Glassmorphism Navbar */}
      <nav className="glass sticky top-0 z-20 border-b border-white/30 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/form')}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-white/60 rounded-lg transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-agro-green-500 rounded-lg flex items-center justify-center shadow-sm">
                <Leaf className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-gray-800 text-sm tracking-tight">AgroPulse AI</span>
            </div>
            {location && (
              <div className="hidden sm:flex items-center gap-1 text-xs text-gray-500 bg-white/60 px-2.5 py-1 rounded-full border border-white/50">
                <MapPin className="w-3 h-3" />
                {location}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-white/60 rounded-lg transition-all">
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-white text-[10px] flex items-center justify-center font-bold animate-pulse-slow">
                  {unreadCount}
                </span>
              )}
            </button>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">

        {/* Hero Header */}
        <div className="animate-fade-in-up">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="w-4 h-4 text-agro-green-500" />
                <span className="text-xs font-semibold text-agro-green-600 uppercase tracking-widest">
                  AI Farm Report
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                Namaste,{' '}
                <span className="text-gradient-green">{farmerName}</span>{' '}
                <span className="text-2xl">🌾</span>
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Your personalized AI farm intelligence report is ready.
              </p>
            </div>
          </div>
        </div>

        {/* Summary Stat Chips */}
        {(cropData || yieldData || priceData) && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {cropData && (
              <div className="animate-scale-in delay-100 bg-white/80 backdrop-blur-sm border border-white/60 rounded-2xl p-4 shadow-card card-hover text-center">
                <div className="text-2xl mb-1">
                  {{ rice: '🌾', wheat: '🌿', maize: '🌽', cotton: '🌱' }[cropData.top_crop] || '🌱'}
                </div>
                <div className="text-xs text-gray-500 mb-0.5">Best Crop</div>
                <div className="text-sm font-bold text-gray-800 capitalize">{cropData.top_crop}</div>
                <div className="text-xs text-agro-green-600 font-medium">{(cropData.confidence * 100).toFixed(0)}% match</div>
              </div>
            )}
            {yieldData && (
              <div className="animate-scale-in delay-200 bg-white/80 backdrop-blur-sm border border-white/60 rounded-2xl p-4 shadow-card card-hover text-center">
                <div className="text-2xl mb-1">📈</div>
                <div className="text-xs text-gray-500 mb-0.5">Total Yield</div>
                <div className="text-sm font-bold text-gray-800">{(yieldData.total_yield_kg / 1000).toFixed(1)}t</div>
                <div className="text-xs text-blue-600 font-medium">{yieldData.predicted_yield_kg_per_hectare.toLocaleString()} kg/ha</div>
              </div>
            )}
            {priceData && (
              <div className="animate-scale-in delay-300 bg-white/80 backdrop-blur-sm border border-white/60 rounded-2xl p-4 shadow-card card-hover text-center">
                <div className="text-2xl mb-1">💰</div>
                <div className="text-xs text-gray-500 mb-0.5">Mandi Price</div>
                <div className="text-sm font-bold text-gray-800">₹{priceData.current_price.toLocaleString()}</div>
                <div className="text-xs text-agro-earth-600 font-medium capitalize">{priceData.price_trend}</div>
              </div>
            )}
            {priceData && (
              <div className="animate-scale-in delay-400 bg-white/80 backdrop-blur-sm border border-white/60 rounded-2xl p-4 shadow-card card-hover text-center">
                <div className="text-2xl mb-1">
                  {{ SELL: '📤', 'SELL NOW': '⚡', HOLD: '⏸️', BUY: '📥' }[priceData.market_signal] || '📊'}
                </div>
                <div className="text-xs text-gray-500 mb-0.5">Market Signal</div>
                <div className="text-sm font-bold text-gray-800">{priceData.market_signal}</div>
                <div className="text-xs text-gray-500 font-medium">AI Recommendation</div>
              </div>
            )}
          </div>
        )}

        {/* Risk Alert Banner */}
        <div className="animate-fade-in-up delay-200">
          <RiskAlertBanner alerts={alerts} onDismiss={(id) => setAlerts(a => a.filter(x => x.id !== id))} />
        </div>

        {/* Main 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Crop Recommendation */}
          {cropData && (
            <div className="animate-fade-in-up delay-300">
              <CropRecommendationCard data={cropData} />
            </div>
          )}

          {/* Yield Prediction */}
          {yieldData && (
            <div className="animate-fade-in-up delay-400">
              <YieldChart data={yieldData} />
            </div>
          )}

          {/* Price Forecast — full width */}
          {priceData && (
            <div className="animate-fade-in-up delay-500 lg:col-span-2">
              <PriceForecastChart data={priceData} />
            </div>
          )}
        </div>

        {/* AI Explanation Panel */}
        {explanation && (
          <div className="animate-fade-in-up delay-600">
            <ExplanationPanel data={explanation} />
          </div>
        )}

        {/* Footer CTA */}
        <div className="animate-fade-in-up delay-700 pb-8">
          <div className="bg-white/60 backdrop-blur-sm border border-white/60 rounded-2xl p-6 text-center shadow-card">
            <p className="text-sm text-gray-500 mb-4">
              Want to update your farm parameters or run a new analysis?
            </p>
            <button
              onClick={() => navigate('/form')}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-agro-green-600 to-agro-green-500 text-white font-semibold rounded-xl shadow-glow-green hover:from-agro-green-700 hover:to-agro-green-600 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
            >
              <RefreshCw className="w-4 h-4" />
              Run New Analysis
            </button>
            <p className="text-[11px] text-gray-400 mt-3">
              Powered by AWS SageMaker · Amazon Bedrock · AgroPulse AI
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

// AgroPulse AI - TypeScript Type Definitions

export interface SoilData {
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  ph: number;
}

export interface LocationData {
  state: string;
  district: string;
  latitude?: number;
  longitude?: number;
}

export interface CropRecommendationRequest {
  soil: SoilData;
  location: LocationData;
  rainfall_mm: number;
  temperature_celsius: number;
  humidity_percent: number;
  farmer_id?: string;
}

export interface CropScore {
  crop_name: string;
  confidence_score: number;
  expected_yield_kg_per_hectare?: number;
  growing_season_days?: number;
  water_requirement_mm?: number;
}

export interface CropRecommendationResponse {
  recommendations: CropScore[];
  top_crop: string;
  confidence: number;
  model_version: string;
  feature_importance: Record<string, number>;
  prediction_id: string;
  location: string;
  generated_at: string;
}

export interface WeatherForecast {
  temperature_celsius: number;
  rainfall_mm: number;
  humidity_percent: number;
  sunshine_hours?: number;
}

export interface YieldPredictionRequest {
  crop: string;
  area_hectares: number;
  soil_nitrogen: number;
  soil_ph: number;
  weather_forecast: WeatherForecast;
  irrigation: boolean;
  fertilizer_type?: string;
}

export interface YieldPredictionResponse {
  crop: string;
  predicted_yield_kg_per_hectare: number;
  total_yield_kg: number;
  confidence_interval_lower: number;
  confidence_interval_upper: number;
  key_factors: Array<{ factor: string; impact: string; value: number | boolean }>;
  prediction_id: string;
  model_version: string;
  generated_at: string;
}

export interface PriceForecastRequest {
  commodity: string;
  state: string;
  district?: string;
  forecast_days: number;
}

export interface PriceForecastPoint {
  date: string;
  predicted_price: number;
  lower_bound: number;
  upper_bound: number;
  trend: string;
}

export interface PriceForecastResponse {
  commodity: string;
  state: string;
  current_price: number;
  unit: string;
  forecast: PriceForecastPoint[];
  price_trend: string;
  market_signal: string;
  prediction_id: string;
  generated_at: string;
}

export interface Alert {
  id: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  risk_score: number;
  is_read: boolean;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface AlertListResponse {
  farmer_id: string;
  total_alerts: number;
  unread_count: number;
  alerts: Alert[];
}

export interface ExplanationRequest {
  prediction_type: string;
  prediction_output: Record<string, unknown>;
  feature_importance?: Record<string, number>;
  confidence_score?: number;
  farmer_context?: Record<string, unknown>;
  language: string;
}

export interface ExplanationResponse {
  explanation: string;
  key_insights: string[];
  risk_mitigation: string[];
  confidence_narrative: string;
  language: string;
  tokens_used?: number;
  model_used: string;
  generated_at: string;
}

export interface FarmerFormData {
  name: string;
  state: string;
  district: string;
  landArea: number;
  cropType: string;
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  ph: number;
  rainfall: number;
  temperature: number;
  humidity: number;
  irrigation: boolean;
  language: string;
}

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type MarketSignal = 'SELL' | 'SELL NOW' | 'HOLD' | 'BUY';

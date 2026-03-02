/**
 * AgroPulse AI - Farmer Input Form
 * 3-step form: Location → Soil Data → Weather/Crop
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import {
  MapPin, Beaker, Cloud, ChevronRight, ChevronLeft,
  Droplets, Thermometer, Wind, Leaf
} from 'lucide-react';
import { predictAPI, explanationAPI } from '../services/api';
import { FarmerFormData } from '../types';

const INDIAN_STATES = [
  'Andhra Pradesh', 'Bihar', 'Gujarat', 'Haryana', 'Karnataka',
  'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Odisha', 'Punjab',
  'Rajasthan', 'Tamil Nadu', 'Telangana', 'Uttar Pradesh', 'West Bengal',
];

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'हिंदी' },
  { code: 'mr', name: 'मराठी' },
  { code: 'te', name: 'తెలుగు' },
  { code: 'kn', name: 'ಕನ್ನಡ' },
  { code: 'ta', name: 'தமிழ்' },
];

const schema = z.object({
  name: z.string().min(2, 'Name required'),
  state: z.string().min(1, 'Select state'),
  district: z.string().min(2, 'District required'),
  landArea: z.number().min(0.1).max(1000),
  nitrogen: z.number().min(0).max(200),
  phosphorus: z.number().min(0).max(200),
  potassium: z.number().min(0).max(300),
  ph: z.number().min(3).max(10),
  rainfall: z.number().min(0).max(3000),
  temperature: z.number().min(5).max(50),
  humidity: z.number().min(0).max(100),
  irrigation: z.boolean(),
  cropType: z.string().optional(),
  language: z.string().default('en'),
});

type FormData = z.infer<typeof schema>;

const STEPS = [
  { icon: MapPin, title: 'Your Location', subtitle: 'Farm details' },
  { icon: Beaker, title: 'Soil Analysis', subtitle: 'NPK & pH values' },
  { icon: Cloud, title: 'Weather & Crop', subtitle: 'Climate data' },
];

const InputField: React.FC<{
  label: string;
  unit?: string;
  error?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
}> = ({ label, unit, error, children, icon }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">
      {label} {unit && <span className="text-gray-400 text-xs">({unit})</span>}
    </label>
    <div className="relative">
      {icon && <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">{icon}</span>}
      <div className={icon ? 'pl-9' : ''}>{children}</div>
    </div>
    {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
  </div>
);

const FarmerInputForm: React.FC = () => {
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    trigger,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      irrigation: true,
      language: 'en',
      nitrogen: 90,
      phosphorus: 42,
      potassium: 43,
      ph: 6.5,
      rainfall: 800,
      temperature: 25,
      humidity: 65,
      landArea: 2,
    },
  });

  const nextStep = async () => {
    const stepFields: (keyof FormData)[][] = [
      ['name', 'state', 'district', 'landArea'],
      ['nitrogen', 'phosphorus', 'potassium', 'ph'],
      ['rainfall', 'temperature', 'humidity'],
    ];
    const valid = await trigger(stepFields[step]);
    if (valid) setStep((s) => Math.min(s + 1, 2));
  };

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    try {
      // Run all predictions in parallel
      const [cropResult, yieldResult, priceResult] = await Promise.all([
        predictAPI.cropRecommendation({
          soil: {
            nitrogen: data.nitrogen,
            phosphorus: data.phosphorus,
            potassium: data.potassium,
            ph: data.ph,
          },
          location: { state: data.state, district: data.district },
          rainfall_mm: data.rainfall,
          temperature_celsius: data.temperature,
          humidity_percent: data.humidity,
        }),
        predictAPI.yieldPrediction({
          crop: data.cropType || 'rice',
          area_hectares: data.landArea,
          soil_nitrogen: data.nitrogen,
          soil_ph: data.ph,
          weather_forecast: {
            temperature_celsius: data.temperature,
            rainfall_mm: data.rainfall / 12,
            humidity_percent: data.humidity,
            sunshine_hours: 7.5,
          },
          irrigation: data.irrigation,
        }),
        predictAPI.priceForecast({
          commodity: data.cropType || 'Rice',
          state: data.state,
          district: data.district,
          forecast_days: 14,
        }),
      ]);

      // Generate GenAI explanation via Bedrock
      const explanation = await explanationAPI.generateExplanation({
        prediction_type: 'crop_recommendation',
        prediction_output: cropResult as unknown as Record<string, unknown>,
        feature_importance: cropResult.feature_importance,
        confidence_score: cropResult.confidence,
        farmer_context: {
          name: data.name,
          district: data.district,
          land_area: data.landArea,
          current_season: 'Kharif',
        },
        language: data.language,
      });

      // Store results for dashboard
      sessionStorage.setItem('crop_result', JSON.stringify(cropResult));
      sessionStorage.setItem('yield_result', JSON.stringify(yieldResult));
      sessionStorage.setItem('price_result', JSON.stringify(priceResult));
      sessionStorage.setItem('explanation', JSON.stringify(explanation));
      sessionStorage.setItem('farmer_data', JSON.stringify(data));

      toast.success('AI analysis complete!');
      navigate('/dashboard');
    } catch (err: any) {
      toast.error('Analysis failed. Please try again.');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-agro-green-600 text-white px-4 py-6">
        <div className="max-w-lg mx-auto">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Leaf className="w-6 h-6" /> AgroPulse AI
          </h1>
          <p className="text-agro-green-100 text-sm mt-1">Farm Analysis — Step {step + 1} of 3</p>

          {/* Step Indicators */}
          <div className="flex items-center gap-2 mt-4">
            {STEPS.map((s, i) => (
              <React.Fragment key={i}>
                <div className={`flex items-center gap-1.5 ${i <= step ? 'text-white' : 'text-agro-green-300'}`}>
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold
                    ${i < step ? 'bg-white text-agro-green-600' :
                      i === step ? 'bg-agro-earth-400 text-white' : 'bg-agro-green-500 text-agro-green-200'}`}>
                    {i < step ? '✓' : i + 1}
                  </div>
                  <span className="text-xs hidden sm:block">{s.title}</span>
                </div>
                {i < 2 && <div className={`flex-1 h-0.5 ${i < step ? 'bg-white' : 'bg-agro-green-500'}`} />}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Form Content */}
      <div className="max-w-lg mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-6">
            {React.createElement(STEPS[step].icon, { className: 'w-6 h-6 text-agro-green-600' })}
            <div>
              <h2 className="font-semibold text-gray-800">{STEPS[step].title}</h2>
              <p className="text-sm text-gray-500">{STEPS[step].subtitle}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)}>
            {/* Step 1: Location */}
            {step === 0 && (
              <div className="space-y-4">
                <InputField label="Your Name" error={errors.name?.message}>
                  <input {...register('name')} placeholder="Ramesh Kumar"
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                </InputField>
                <InputField label="State" error={errors.state?.message}>
                  <select {...register('state')}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none bg-white">
                    <option value="">Select state</option>
                    {INDIAN_STATES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </InputField>
                <InputField label="District" error={errors.district?.message}>
                  <input {...register('district')} placeholder="e.g. Pune, Ludhiana"
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                </InputField>
                <InputField label="Land Area" unit="hectares" error={errors.landArea?.message}>
                  <input {...register('landArea', { valueAsNumber: true })} type="number" step="0.1" min="0.1"
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                </InputField>
                <InputField label="Preferred Language">
                  <select {...register('language')}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none bg-white">
                    {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
                  </select>
                </InputField>
              </div>
            )}

            {/* Step 2: Soil Data */}
            {step === 1 && (
              <div className="space-y-4">
                <div className="p-3 bg-agro-green-50 rounded-xl text-sm text-agro-green-700">
                  💡 Get NPK values from your Soil Health Card (soilhealth.dac.gov.in)
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Nitrogen (N)" unit="kg/ha" error={errors.nitrogen?.message}>
                    <input {...register('nitrogen', { valueAsNumber: true })} type="number"
                      className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                  </InputField>
                  <InputField label="Phosphorus (P)" unit="kg/ha" error={errors.phosphorus?.message}>
                    <input {...register('phosphorus', { valueAsNumber: true })} type="number"
                      className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                  </InputField>
                  <InputField label="Potassium (K)" unit="kg/ha" error={errors.potassium?.message}>
                    <input {...register('potassium', { valueAsNumber: true })} type="number"
                      className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                  </InputField>
                  <InputField label="Soil pH" error={errors.ph?.message}>
                    <input {...register('ph', { valueAsNumber: true })} type="number" step="0.1" min="3" max="10"
                      className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                  </InputField>
                </div>
                {/* pH Indicator */}
                <div className="bg-gray-50 rounded-xl p-3 text-xs text-gray-600">
                  <strong>pH Guide:</strong> &lt;5.5 Acidic | 6.0–7.5 Ideal | &gt;8.0 Alkaline
                  <div className="flex gap-1 mt-2 h-2 rounded-full overflow-hidden">
                    <div className="flex-1 bg-red-300" />
                    <div className="flex-1 bg-yellow-300" />
                    <div className="flex-1 bg-agro-green-400" />
                    <div className="flex-1 bg-yellow-300" />
                    <div className="flex-1 bg-blue-300" />
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Weather & Crop */}
            {step === 2 && (
              <div className="space-y-4">
                <InputField label="Annual Rainfall" unit="mm" error={errors.rainfall?.message}>
                  <input {...register('rainfall', { valueAsNumber: true })} type="number"
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                </InputField>
                <div className="grid grid-cols-2 gap-4">
                  <InputField label="Temperature" unit="°C" error={errors.temperature?.message}>
                    <input {...register('temperature', { valueAsNumber: true })} type="number" step="0.5"
                      className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                  </InputField>
                  <InputField label="Humidity" unit="%" error={errors.humidity?.message}>
                    <input {...register('humidity', { valueAsNumber: true })} type="number"
                      className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                  </InputField>
                </div>
                <InputField label="Current/Target Crop (optional)">
                  <input {...register('cropType')} placeholder="e.g. Rice, Wheat, Cotton"
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-agro-green-400 outline-none" />
                </InputField>
                <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-xl">
                  <input {...register('irrigation')} type="checkbox" id="irrigation"
                    className="w-5 h-5 text-agro-green-500 rounded" />
                  <label htmlFor="irrigation" className="text-sm text-gray-700 font-medium">
                    <Droplets className="w-4 h-4 inline mr-1 text-blue-500" />
                    Irrigation Available
                  </label>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex gap-3 mt-6">
              {step > 0 && (
                <button type="button" onClick={() => setStep(s => s - 1)}
                  className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-gray-50">
                  <ChevronLeft className="w-4 h-4" /> Back
                </button>
              )}
              {step < 2 ? (
                <button type="button" onClick={nextStep}
                  className="flex-1 py-3 bg-agro-green-600 text-white rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-agro-green-700">
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button type="submit" disabled={isSubmitting}
                  className="flex-1 py-3 bg-agro-earth-500 text-white rounded-xl font-semibold flex items-center justify-center gap-2 hover:bg-agro-earth-600 disabled:opacity-50">
                  {isSubmitting ? (
                    <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Analyzing...</>
                  ) : (
                    <><Leaf className="w-5 h-5" /> Get AI Insights</>
                  )}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default FarmerInputForm;

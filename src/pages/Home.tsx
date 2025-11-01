import { useEffect, useState } from 'react';
import { Zap, Thermometer, Droplets, Clock, Calendar } from 'lucide-react';
import { supabase, SensorReading, SystemStatus } from '../lib/supabase';

interface WeatherData {
  condition: string;
  icon: string;
  temperature: number;
}

export default function Home() {
  const [sensorData, setSensorData] = useState<SensorReading | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [weather] = useState<WeatherData>({
    condition: 'Sunny',
    icon: '☀️',
    temperature: 28
  });
  const [generationData, setGenerationData] = useState<Array<{ time: string; value: number }>>([]);

  useEffect(() => {
    fetchLatestData();
    const interval = setInterval(() => {
      fetchLatestData();
      setCurrentTime(new Date());
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const fetchLatestData = async () => {
    const { data: sensorReading } = await supabase
      .from('sensor_readings')
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (sensorReading) {
      setSensorData(sensorReading);
    }

    const { data: status } = await supabase
      .from('system_status')
      .select('*')
      .limit(1)
      .maybeSingle();

    if (status) {
      setSystemStatus(status);
    }

    const { data: recentReadings } = await supabase
      .from('sensor_readings')
      .select('wattage, timestamp')
      .order('timestamp', { ascending: false })
      .limit(20);

    if (recentReadings) {
      const chartData = recentReadings.reverse().map((reading) => ({
        time: new Date(reading.timestamp).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        }),
        value: Number(reading.wattage)
      }));
      setGenerationData(chartData);
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const maxWattage = Math.max(...generationData.map(d => d.value), 100);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-amber-300 transition-all shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-gray-600 text-sm font-medium">Voltage</span>
            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {sensorData?.voltage.toFixed(2) || '0.00'}
            <span className="text-lg text-gray-500 ml-2">V</span>
          </div>
          <div className="text-xs text-gray-500">Live reading</div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-amber-300 transition-all shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-gray-600 text-sm font-medium">Power Output</span>
            <div className="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-amber-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {sensorData?.wattage.toFixed(2) || '0.00'}
            <span className="text-lg text-gray-500 ml-2">W</span>
          </div>
          <div className="text-xs text-gray-500">Current generation</div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-amber-300 transition-all shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-gray-600 text-sm font-medium">Current</span>
            <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-purple-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {sensorData?.ampere.toFixed(2) || '0.00'}
            <span className="text-lg text-gray-500 ml-2">A</span>
          </div>
          <div className="text-xs text-gray-500">Live reading</div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-amber-300 transition-all shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-gray-600 text-sm font-medium">Temperature</span>
            <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
              <Thermometer className="w-5 h-5 text-red-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {sensorData?.temperature.toFixed(1) || '0.0'}
            <span className="text-lg text-gray-500 ml-2">°C</span>
          </div>
          <div className="text-xs text-gray-500">Ambient temperature</div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-amber-300 transition-all shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-gray-600 text-sm font-medium">Humidity</span>
            <div className="w-10 h-10 bg-cyan-50 rounded-lg flex items-center justify-center">
              <Droplets className="w-5 h-5 text-cyan-600" />
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {sensorData?.humidity.toFixed(1) || '0.0'}
            <span className="text-lg text-gray-500 ml-2">%</span>
          </div>
          <div className="text-xs text-gray-500">Relative humidity</div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-amber-300 transition-all shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-gray-600 text-sm font-medium">System Uptime</span>
            <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <div className="text-2xl font-bold text-gray-900 mb-1">
            {systemStatus ? formatUptime(systemStatus.uptime_seconds) : '0d 0h 0m'}
          </div>
          <div className="text-xs text-gray-500">Continuous operation</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Power Generation</h3>
            <span className="text-sm text-gray-500">Last 20 readings</span>
          </div>

          <div className="relative h-64">
            <div className="absolute inset-0 flex items-end justify-between gap-1">
              {generationData.length > 0 ? (
                generationData.map((point, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center group">
                    <div
                      className="w-full bg-gradient-to-t from-amber-500 to-orange-400 rounded-t transition-all hover:from-amber-600 hover:to-orange-500"
                      style={{ height: `${(point.value / maxWattage) * 100}%`, minHeight: '4px' }}
                    >
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 px-2 py-1 rounded text-xs text-white whitespace-nowrap transition-opacity">
                        {point.value.toFixed(1)}W
                      </div>
                    </div>
                    {index % 4 === 0 && (
                      <span className="text-xs text-gray-500 mt-2">{point.time}</span>
                    )}
                  </div>
                ))
              ) : (
                <div className="flex items-center justify-center w-full h-full text-gray-400">
                  No data available
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-center gap-6 mt-6 pt-6 border-t border-gray-200">
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-600">
                {generationData.length > 0
                  ? (generationData.reduce((acc, d) => acc + d.value, 0) / generationData.length).toFixed(1)
                  : '0.0'}W
              </div>
              <div className="text-xs text-gray-500 mt-1">Average</div>
            </div>
            <div className="w-px h-10 bg-gray-200"></div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Math.max(...generationData.map(d => d.value), 0).toFixed(1)}W
              </div>
              <div className="text-xs text-gray-500 mt-1">Peak</div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <Calendar className="w-5 h-5 text-amber-600" />
              <h3 className="text-lg font-semibold text-gray-900">Current Time</h3>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {currentTime.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })}
            </div>
            <div className="text-gray-600">
              {currentTime.toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric'
              })}
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-4xl">{weather.icon}</span>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{weather.condition}</h3>
                <p className="text-sm text-gray-600">Weather Conditions</p>
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold text-gray-900">{weather.temperature}°</span>
              <span className="text-gray-600">Celsius</span>
            </div>
            <div className="mt-4 pt-4 border-t border-blue-200">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Optimal for generation</span>
                <span className="text-green-600 font-medium">Excellent</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

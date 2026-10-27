import { useEffect, useState } from 'react';
import { RotateCcw, Power, Save, Trash2, Plus } from 'lucide-react';
import { supabase, PanelPosition, AngleCurve } from '../lib/supabase';
import SolarPanel3D from '../components/SolarPanel3D';

export default function Control() {
  const [position, setPosition] = useState<PanelPosition>({
    id: '',
    vertical_angle: 90,
    horizontal_angle: 0,
    timestamp: new Date().toISOString()
  });
  const [curves, setCurves] = useState<AngleCurve[]>([]);
  const [newCurve, setNewCurve] = useState({
    time_hour: 6,
    time_minute: 0,
    vertical_angle: 90,
    horizontal_angle: 0
  });
  const [showAddCurve, setShowAddCurve] = useState(false);

  useEffect(() => {
    fetchPosition();
    fetchCurves();
  }, []);

  const fetchPosition = async () => {
    const { data } = await supabase
      .from('panel_position')
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(1)
      .maybeSingle();

    if (data) {
      setPosition(data);
    }
  };

  const fetchCurves = async () => {
    const { data } = await supabase
      .from('angle_curves')
      .select('*')
      .eq('is_active', true)
      .order('time_hour', { ascending: true })
      .order('time_minute', { ascending: true });

    if (data) {
      setCurves(data);
    }
  };

  const updatePosition = async (vertical: number, horizontal: number) => {
    await supabase
      .from('panel_position')
      .insert({
        vertical_angle: vertical,
        horizontal_angle: horizontal
      });

    fetchPosition();
  };

  const handleRecalibrate = async () => {
    await updatePosition(90, 0);
  };

  const handleReset = async () => {
    await updatePosition(90, 180);
  };

  const handleSleepMode = async () => {
    await updatePosition(35, 0);
    await supabase
      .from('system_status')
      .update({ status: 'sleep' })
      .eq('id', (await supabase.from('system_status').select('id').limit(1).maybeSingle())?.data?.id || '');
  };

  const handleAddCurve = async () => {
    await supabase
      .from('angle_curves')
      .insert(newCurve);

    setNewCurve({
      time_hour: 6,
      time_minute: 0,
      vertical_angle: 90,
      horizontal_angle: 0
    });
    setShowAddCurve(false);
    fetchCurves();
  };

  const handleDeleteCurve = async (id: string) => {
    await supabase
      .from('angle_curves')
      .delete()
      .eq('id', id);

    fetchCurves();
  };

  const handleApplyCurves = async () => {
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();

    const activeCurve = curves.find(curve => {
      if (curve.time_hour === currentHour) {
        return curve.time_minute <= currentMinute;
      }
      return curve.time_hour < currentHour;
    });

    if (activeCurve) {
      await updatePosition(activeCurve.vertical_angle, activeCurve.horizontal_angle);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Solar Panel Position</h3>
          <SolarPanel3D
            verticalAngle={position.vertical_angle}
            horizontalAngle={position.horizontal_angle}
          />
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Position</h3>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-600 mb-2 block">
                  Vertical Angle (35° - 145°)
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="35"
                    max="145"
                    value={position.vertical_angle}
                    onChange={(e) => setPosition({ ...position, vertical_angle: Number(e.target.value) })}
                    className="flex-1 h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #f59e0b 0%, #f59e0b ${((position.vertical_angle - 35) / (145 - 35)) * 100}%, #e5e7eb ${((position.vertical_angle - 35) / (145 - 35)) * 100}%, #e5e7eb 100%)`
                    }}
                  />
                  <span className="text-gray-900 font-semibold w-16 text-right">
                    {position.vertical_angle.toFixed(0)}°
                  </span>
                </div>
              </div>

              <div>
                <label className="text-sm text-gray-600 mb-2 block">
                  Horizontal Angle (0° - 360°)
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="0"
                    max="360"
                    value={position.horizontal_angle}
                    onChange={(e) => setPosition({ ...position, horizontal_angle: Number(e.target.value) })}
                    className="flex-1 h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #f59e0b 0%, #f59e0b ${(position.horizontal_angle / 360) * 100}%, #e5e7eb ${(position.horizontal_angle / 360) * 100}%, #e5e7eb 100%)`
                    }}
                  />
                  <span className="text-gray-900 font-semibold w-16 text-right">
                    {position.horizontal_angle.toFixed(0)}°
                  </span>
                </div>
              </div>

              <button
                onClick={() => updatePosition(position.vertical_angle, position.horizontal_angle)}
                className="w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white font-semibold py-3 rounded-lg hover:from-amber-600 hover:to-orange-600 transition-all shadow-sm"
              >
                Update Position
              </button>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handleRecalibrate}
                className="flex items-center justify-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-900 font-medium py-3 rounded-lg transition-all"
              >
                <RotateCcw className="w-4 h-4" />
                Recalibrate
              </button>
              <button
                onClick={handleReset}
                className="flex items-center justify-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-900 font-medium py-3 rounded-lg transition-all"
              >
                <RotateCcw className="w-4 h-4" />
                Reset
              </button>
              <button
                onClick={handleSleepMode}
                className="col-span-2 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-all"
              >
                <Power className="w-4 h-4" />
                Enter Sleep Mode
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Angle Adjustment Curves</h3>
            <p className="text-sm text-gray-600 mt-1">Configure automated position adjustments based on time (6AM - 6PM)</p>
          </div>
          <button
            onClick={() => setShowAddCurve(true)}
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-medium px-4 py-2 rounded-lg transition-all"
          >
            <Plus className="w-4 h-4" />
            Add Point
          </button>
        </div>

        {showAddCurve && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-300">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Hour (6-18)</label>
                <input
                  type="number"
                  min="6"
                  max="18"
                  value={newCurve.time_hour}
                  onChange={(e) => setNewCurve({ ...newCurve, time_hour: Number(e.target.value) })}
                  className="w-full bg-white border border-gray-300 text-gray-900 px-3 py-2 rounded"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Minute</label>
                <input
                  type="number"
                  min="0"
                  max="59"
                  value={newCurve.time_minute}
                  onChange={(e) => setNewCurve({ ...newCurve, time_minute: Number(e.target.value) })}
                  className="w-full bg-white border border-gray-300 text-gray-900 px-3 py-2 rounded"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Vertical °</label>
                <input
                  type="number"
                  min="35"
                  max="145"
                  value={newCurve.vertical_angle}
                  onChange={(e) => setNewCurve({ ...newCurve, vertical_angle: Number(e.target.value) })}
                  className="w-full bg-white border border-gray-300 text-gray-900 px-3 py-2 rounded"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Horizontal °</label>
                <input
                  type="number"
                  min="0"
                  max="360"
                  value={newCurve.horizontal_angle}
                  onChange={(e) => setNewCurve({ ...newCurve, horizontal_angle: Number(e.target.value) })}
                  className="w-full bg-white border border-gray-300 text-gray-900 px-3 py-2 rounded"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleAddCurve}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 rounded-lg transition-all"
              >
                Add
              </button>
              <button
                onClick={() => setShowAddCurve(false)}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-900 font-medium py-2 rounded-lg transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="space-y-2 mb-4">
          {curves.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No angle curves configured. Add points to enable automated tracking.
            </div>
          ) : (
            curves.map((curve) => (
              <div
                key={curve.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-amber-300 transition-all"
              >
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">
                      {String(curve.time_hour).padStart(2, '0')}:{String(curve.time_minute).padStart(2, '0')}
                    </div>
                    <div className="text-xs text-gray-500">Time</div>
                  </div>
                  <div className="w-px h-10 bg-gray-300"></div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-amber-600">{curve.vertical_angle}°</div>
                    <div className="text-xs text-gray-500">Vertical</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-orange-600">{curve.horizontal_angle}°</div>
                    <div className="text-xs text-gray-500">Horizontal</div>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteCurve(curve.id)}
                  className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>

        <button
          onClick={handleApplyCurves}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-3 rounded-lg transition-all shadow-sm"
        >
          <Save className="w-5 h-5" />
          Apply Current Curve
        </button>
      </div>
    </div>
  );
}

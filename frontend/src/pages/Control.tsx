import { useEffect, useState } from 'react';
import { RotateCcw, Power, Save, Trash2, Plus, Sun, Pause, Play } from 'lucide-react';
import { api, Angles, CurvePoint, PanelState } from '../lib/api';
import SolarPanel3D from '../components/SolarPanel3D';

// Run an API action, surfacing failures the same way the rest of the dashboard does
const run = async (action: () => Promise<unknown>) => {
  try {
    await action();
  } catch (e) {
    alert(e instanceof Error ? e.message : String(e));
  }
};

export default function Control() {
  const [panel, setPanel] = useState<PanelState | null>(null);
  const [target, setTarget] = useState<Angles | null>(null);
  const [trackingEnabled, setTrackingEnabled] = useState(true);
  const [curves, setCurves] = useState<CurvePoint[]>([]);
  const [newPoint, setNewPoint] = useState<CurvePoint>({ time: '06:30', yaw: 90, roll: 90 });
  const [showAddCurve, setShowAddCurve] = useState(false);

  useEffect(() => {
    fetchPanel(true);
    fetchCurves();
    api.system.tracking().then((t) => setTrackingEnabled(t.enabled)).catch(() => {});

    // Poll so the 3D view follows the panel while the tracking loop moves it
    const interval = setInterval(() => fetchPanel(false), 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchPanel = async (resetTarget: boolean) => {
    try {
      const state = await api.panel.state();
      setPanel(state);
      if (resetTarget) setTarget(state.expected);
    } catch {
      // Backend unreachable; keep showing the last known state
    }
  };

  const fetchCurves = async () => {
    try {
      setCurves(await api.panel.curves());
    } catch {
      // Backend unreachable; keep the last known curves
    }
  };

  const updatePosition = (angles: Angles) =>
    run(async () => {
      await api.panel.setAngle(angles);
      setTarget(angles);
      await fetchPanel(false);
    });

  const handleRecalibrate = () => {
    if (panel) updatePosition({ yaw: panel.range.yaw[0], roll: 90 });
  };

  const handleReset = () => updatePosition({ yaw: 90, roll: 90 });

  const handleSleepMode = () =>
    run(async () => {
      await api.system.setStatus('sleep');
      await fetchPanel(true);
    });

  const handleToggleTracking = () =>
    run(async () => {
      const status = await api.system.setTracking(!trackingEnabled);
      setTrackingEnabled(status.enabled);
    });

  const handleAddCurve = () =>
    run(async () => {
      await api.panel.upsertCurvePoint(newPoint);
      setNewPoint({ time: '06:30', yaw: 90, roll: 90 });
      setShowAddCurve(false);
      await fetchCurves();
    });

  const handleDeleteCurve = (time: string) =>
    run(async () => {
      await api.panel.deleteCurvePoint(time);
      await fetchCurves();
    });

  const handleLoadOptimal = () => {
    if (curves.length > 0 && !confirm('Replace the current schedule with today\'s optimal angles?')) return;
    run(async () => {
      const optimal = await api.panel.optimal();
      setCurves(await api.panel.replaceCurves(optimal.map(({ time, yaw, roll }) => ({ time, yaw, roll }))));
    });
  };

  const handleApplyCurves = () =>
    run(async () => {
      setTarget(await api.panel.applyCurrentCurve());
      await fetchPanel(false);
    });

  const yawRange = panel?.range.yaw ?? [0, 180];
  const rollRange = panel?.range.roll ?? [35, 145];
  const realtime = panel?.realtime ?? { yaw: 90, roll: 90 };
  const slider = target ?? realtime;

  const sliderBackground = (value: number, [min, max]: [number, number]) => {
    const pct = ((value - min) / (max - min)) * 100;
    return `linear-gradient(to right, #f59e0b 0%, #f59e0b ${pct}%, #e5e7eb ${pct}%, #e5e7eb 100%)`;
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Solar Panel Position</h3>
          <SolarPanel3D
            verticalAngle={realtime.roll}
            horizontalAngle={realtime.yaw}
          />
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Current Position</h3>
              <span className="text-sm text-gray-500">
                Now: yaw {realtime.yaw.toFixed(0)}°, roll {realtime.roll.toFixed(0)}°
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-600 mb-2 block">
                  Roll ({rollRange[0]}° - {rollRange[1]}°)
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min={rollRange[0]}
                    max={rollRange[1]}
                    value={slider.roll}
                    onChange={(e) => setTarget({ ...slider, roll: Number(e.target.value) })}
                    className="flex-1 h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer"
                    style={{ background: sliderBackground(slider.roll, rollRange) }}
                  />
                  <span className="text-gray-900 font-semibold w-16 text-right">
                    {slider.roll.toFixed(0)}°
                  </span>
                </div>
              </div>

              <div>
                <label className="text-sm text-gray-600 mb-2 block">
                  Yaw ({yawRange[0]}° - {yawRange[1]}°)
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min={yawRange[0]}
                    max={yawRange[1]}
                    value={slider.yaw}
                    onChange={(e) => setTarget({ ...slider, yaw: Number(e.target.value) })}
                    className="flex-1 h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer"
                    style={{ background: sliderBackground(slider.yaw, yawRange) }}
                  />
                  <span className="text-gray-900 font-semibold w-16 text-right">
                    {slider.yaw.toFixed(0)}°
                  </span>
                </div>
              </div>

              <button
                onClick={() => updatePosition(slider)}
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
                onClick={handleToggleTracking}
                className="flex items-center justify-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-900 font-medium py-3 rounded-lg transition-all"
              >
                {trackingEnabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {trackingEnabled ? 'Pause Tracking' : 'Resume Tracking'}
              </button>
              <button
                onClick={handleSleepMode}
                className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-all"
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
            <p className="text-sm text-gray-600 mt-1">Configure automated position adjustments based on time of day</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleLoadOptimal}
              className="flex items-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-900 font-medium px-4 py-2 rounded-lg transition-all"
            >
              <Sun className="w-4 h-4" />
              Load Optimal
            </button>
            <button
              onClick={() => setShowAddCurve(true)}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-medium px-4 py-2 rounded-lg transition-all"
            >
              <Plus className="w-4 h-4" />
              Add Point
            </button>
          </div>
        </div>

        {showAddCurve && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-300">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Time</label>
                <input
                  type="time"
                  value={newPoint.time}
                  onChange={(e) => setNewPoint({ ...newPoint, time: e.target.value })}
                  className="w-full bg-white border border-gray-300 text-gray-900 px-3 py-2 rounded"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Yaw °</label>
                <input
                  type="number"
                  min={yawRange[0]}
                  max={yawRange[1]}
                  value={newPoint.yaw}
                  onChange={(e) => setNewPoint({ ...newPoint, yaw: Number(e.target.value) })}
                  className="w-full bg-white border border-gray-300 text-gray-900 px-3 py-2 rounded"
                />
              </div>
              <div>
                <label className="text-xs text-gray-600 mb-1 block">Roll °</label>
                <input
                  type="number"
                  min={rollRange[0]}
                  max={rollRange[1]}
                  value={newPoint.roll}
                  onChange={(e) => setNewPoint({ ...newPoint, roll: Number(e.target.value) })}
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
              No angle curves configured. Add points or load the optimal curve to enable automated tracking.
            </div>
          ) : (
            curves.map((curve) => (
              <div
                key={curve.time}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-amber-300 transition-all"
              >
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{curve.time}</div>
                    <div className="text-xs text-gray-500">Time</div>
                  </div>
                  <div className="w-px h-10 bg-gray-300"></div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-amber-600">{curve.roll}°</div>
                    <div className="text-xs text-gray-500">Roll</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-orange-600">{curve.yaw}°</div>
                    <div className="text-xs text-gray-500">Yaw</div>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteCurve(curve.time)}
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

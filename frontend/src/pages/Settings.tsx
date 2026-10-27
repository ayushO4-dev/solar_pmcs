import { useEffect, useState } from 'react';
import { Save, Download, Terminal, Power, Lock } from 'lucide-react';
import { supabase, SystemConfig, SensorOffset, SystemStatus } from '../lib/supabase';

export default function Settings() {
  const [apiServer, setApiServer] = useState('');
  const [offsets, setOffsets] = useState<Record<string, number>>({
    voltage: 0,
    wattage: 0,
    ampere: 0,
    temperature: 0,
    humidity: 0
  });
  const [firmwareVersion, setFirmwareVersion] = useState('1.0.0');
  const [sshPassword, setSshPassword] = useState('');
  const [showTerminal, setShowTerminal] = useState(false);
  const [terminalCommand, setTerminalCommand] = useState('');
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    const { data: config } = await supabase
      .from('system_config')
      .select('*')
      .eq('key', 'api_server_address')
      .maybeSingle();

    if (config) {
      setApiServer(config.value);
    }

    const { data: offsetData } = await supabase
      .from('sensor_offsets')
      .select('*');

    if (offsetData) {
      const offsetMap: Record<string, number> = {};
      offsetData.forEach(offset => {
        offsetMap[offset.sensor_type] = offset.offset_value;
      });
      setOffsets(offsetMap);
    }

    const { data: status } = await supabase
      .from('system_status')
      .select('firmware_version')
      .limit(1)
      .maybeSingle();

    if (status) {
      setFirmwareVersion(status.firmware_version);
    }
  };

  const handleSaveApiServer = async () => {
    await supabase
      .from('system_config')
      .update({ value: apiServer })
      .eq('key', 'api_server_address');

    alert('API server address updated successfully!');
  };

  const handleSaveOffsets = async () => {
    for (const [sensorType, value] of Object.entries(offsets)) {
      await supabase
        .from('sensor_offsets')
        .update({ offset_value: value })
        .eq('sensor_type', sensorType);
    }

    alert('Sensor offsets updated successfully!');
  };

  const handleExportData = async () => {
    const { data: readings } = await supabase
      .from('sensor_readings')
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(1000);

    if (readings) {
      const csv = [
        'Timestamp,Voltage,Wattage,Ampere,Temperature,Humidity',
        ...readings.map(r =>
          `${r.timestamp},${r.voltage},${r.wattage},${r.ampere},${r.temperature},${r.humidity}`
        )
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `solar_data_${new Date().toISOString()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleTerminalAuth = () => {
    if (sshPassword === 'admin123') {
      setIsAuthenticated(true);
      setTerminalOutput(['Authentication successful. Terminal ready.']);
    } else {
      alert('Incorrect password!');
    }
  };

  const handleTerminalCommand = () => {
    if (!terminalCommand.trim()) return;

    const output = [...terminalOutput];
    output.push(`$ ${terminalCommand}`);

    if (terminalCommand === 'help') {
      output.push('Available commands: status, uptime, clear, exit');
    } else if (terminalCommand === 'status') {
      output.push('System Status: Active');
      output.push(`Firmware: ${firmwareVersion}`);
    } else if (terminalCommand === 'uptime') {
      output.push('System uptime: 2 days, 5 hours, 32 minutes');
    } else if (terminalCommand === 'clear') {
      setTerminalOutput([]);
      setTerminalCommand('');
      return;
    } else if (terminalCommand === 'exit') {
      setShowTerminal(false);
      setIsAuthenticated(false);
      setTerminalOutput([]);
      setTerminalCommand('');
      return;
    } else {
      output.push(`Command not found: ${terminalCommand}`);
    }

    setTerminalOutput(output);
    setTerminalCommand('');
  };

  const handleSystemAction = async (action: string) => {
    if (confirm(`Are you sure you want to ${action} the system?`)) {
      await supabase
        .from('system_status')
        .update({ status: action })
        .eq('id', (await supabase.from('system_status').select('id').limit(1).maybeSingle())?.data?.id || '');

      alert(`System ${action} initiated!`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">API Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-600 mb-2 block">API Server Address</label>
            <input
              type="text"
              value={apiServer}
              onChange={(e) => setApiServer(e.target.value)}
              className="w-full bg-white border border-gray-300 text-gray-900 px-4 py-3 rounded-lg focus:outline-none focus:border-amber-500"
              placeholder="http://localhost:3000"
            />
          </div>
          <button
            onClick={handleSaveApiServer}
            className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-medium px-6 py-2 rounded-lg transition-all"
          >
            <Save className="w-4 h-4" />
            Save API Settings
          </button>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sensor Calibration Offsets</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          {Object.entries(offsets).map(([sensor, value]) => (
            <div key={sensor}>
              <label className="text-sm text-gray-600 mb-2 block capitalize">{sensor}</label>
              <input
                type="number"
                step="0.01"
                value={value}
                onChange={(e) => setOffsets({ ...offsets, [sensor]: Number(e.target.value) })}
                className="w-full bg-white border border-gray-300 text-gray-900 px-4 py-3 rounded-lg focus:outline-none focus:border-amber-500"
              />
            </div>
          ))}
        </div>
        <button
          onClick={handleSaveOffsets}
          className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-medium px-6 py-2 rounded-lg transition-all"
        >
          <Save className="w-4 h-4" />
          Save Offsets
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Export</h3>
        <p className="text-gray-600 text-sm mb-4">Export sensor readings to CSV format</p>
        <button
          onClick={handleExportData}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-medium px-6 py-2 rounded-lg transition-all"
        >
          <Download className="w-4 h-4" />
          Export Data (CSV)
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">Firmware Version</div>
            <div className="text-xl font-semibold text-gray-900">{firmwareVersion}</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">System Architecture</div>
            <div className="text-xl font-semibold text-gray-900">ARM64</div>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">SSH Terminal</h3>
        {!showTerminal ? (
          <button
            onClick={() => setShowTerminal(true)}
            className="flex items-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-900 font-medium px-6 py-2 rounded-lg transition-all"
          >
            <Terminal className="w-4 h-4" />
            Open Terminal
          </button>
        ) : (
          <div className="space-y-4">
            {!isAuthenticated ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-gray-600 text-sm">
                  <Lock className="w-4 h-4" />
                  <span>Terminal access is password protected</span>
                </div>
                <input
                  type="password"
                  value={sshPassword}
                  onChange={(e) => setSshPassword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleTerminalAuth()}
                  className="w-full bg-white border border-gray-300 text-gray-900 px-4 py-3 rounded-lg focus:outline-none focus:border-amber-500"
                  placeholder="Enter password (default: admin123)"
                />
                <button
                  onClick={handleTerminalAuth}
                  className="w-full bg-amber-500 hover:bg-amber-600 text-white font-medium py-2 rounded-lg transition-all"
                >
                  Authenticate
                </button>
              </div>
            ) : (
              <div>
                <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 font-mono text-sm mb-3 h-64 overflow-y-auto">
                  {terminalOutput.map((line, i) => (
                    <div key={i} className={line.startsWith('$') ? 'text-green-400' : 'text-gray-300'}>
                      {line}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={terminalCommand}
                    onChange={(e) => setTerminalCommand(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleTerminalCommand()}
                    className="flex-1 bg-white border border-gray-300 text-gray-900 px-4 py-2 rounded-lg focus:outline-none focus:border-amber-500 font-mono"
                    placeholder="Type command (try 'help')"
                  />
                  <button
                    onClick={handleTerminalCommand}
                    className="bg-green-600 hover:bg-green-700 text-white font-medium px-6 py-2 rounded-lg transition-all"
                  >
                    Run
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Controls</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button
            onClick={() => handleSystemAction('reboot')}
            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-all"
          >
            <Power className="w-4 h-4" />
            Reboot System
          </button>
          <button
            onClick={() => handleSystemAction('shutdown')}
            className="flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white font-medium py-3 rounded-lg transition-all"
          >
            <Power className="w-4 h-4" />
            Shutdown
          </button>
          <button
            onClick={() => handleSystemAction('sleep')}
            className="flex items-center justify-center gap-2 bg-gray-500 hover:bg-gray-600 text-white font-medium py-3 rounded-lg transition-all"
          >
            <Power className="w-4 h-4" />
            Sleep Mode
          </button>
        </div>
      </div>
    </div>
  );
}

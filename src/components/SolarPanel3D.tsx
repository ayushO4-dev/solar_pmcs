import { useEffect, useRef } from 'react';

interface SolarPanel3DProps {
  verticalAngle: number;
  horizontalAngle: number;
}

export default function SolarPanel3D({ verticalAngle, horizontalAngle }: SolarPanel3DProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const rad = (horizontalAngle * Math.PI) / 180;
    const vertRad = ((verticalAngle - 90) * Math.PI) / 180;

    const baseRadius = 40;
    const baseHeight = 20;
    ctx.fillStyle = '#1e293b';
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.ellipse(centerX, centerY + 120, baseRadius, 15, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    const cylinderTop = centerY + 120 - baseHeight;
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(centerX - 25, cylinderTop, 50, baseHeight);
    ctx.strokeRect(centerX - 25, cylinderTop, 50, baseHeight);

    ctx.beginPath();
    ctx.ellipse(centerX, cylinderTop, 25, 10, 0, 0, Math.PI * 2);
    ctx.fillStyle = '#1e293b';
    ctx.fill();
    ctx.stroke();

    const poleHeight = 60;
    const poleTop = cylinderTop - poleHeight;
    ctx.fillStyle = '#334155';
    ctx.fillRect(centerX - 5, poleTop, 10, poleHeight);
    ctx.strokeRect(centerX - 5, poleTop, 10, poleHeight);

    const panelWidth = 160;
    const panelHeight = 100;
    const tilt = Math.sin(vertRad) * 30;
    const panelCenterY = poleTop - 20;

    ctx.save();
    ctx.translate(centerX, panelCenterY);
    ctx.rotate(rad);

    const cornerOffsetY = tilt;
    const perspective = 0.6;

    const corners = [
      { x: -panelWidth / 2, y: -panelHeight / 2 + cornerOffsetY },
      { x: panelWidth / 2, y: -panelHeight / 2 + cornerOffsetY },
      { x: panelWidth / 2 * perspective, y: panelHeight / 2 - cornerOffsetY },
      { x: -panelWidth / 2 * perspective, y: panelHeight / 2 - cornerOffsetY }
    ];

    const gradient = ctx.createLinearGradient(0, -panelHeight / 2, 0, panelHeight / 2);
    gradient.addColorStop(0, '#1e40af');
    gradient.addColorStop(0.5, '#3b82f6');
    gradient.addColorStop(1, '#1e3a8a');

    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    corners.forEach(corner => ctx.lineTo(corner.x, corner.y));
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
    ctx.strokeStyle = '#1e3a8a';
    ctx.lineWidth = 3;
    ctx.stroke();

    ctx.strokeStyle = '#60a5fa';
    ctx.lineWidth = 1;
    for (let i = 1; i < 4; i++) {
      const x = -panelWidth / 2 + (panelWidth / 4) * i;
      ctx.beginPath();
      ctx.moveTo(x, -panelHeight / 2 + cornerOffsetY);
      ctx.lineTo(x * perspective, panelHeight / 2 - cornerOffsetY);
      ctx.stroke();
    }

    for (let i = 1; i < 3; i++) {
      const y = -panelHeight / 2 + (panelHeight / 3) * i;
      const yBottom = panelHeight / 2 - (panelHeight / 3) * (3 - i);
      ctx.beginPath();
      ctx.moveTo(-panelWidth / 2, y + cornerOffsetY);
      ctx.lineTo(panelWidth / 2, y + cornerOffsetY);
      ctx.stroke();
    }

    ctx.restore();

    ctx.fillStyle = 'rgba(251, 191, 36, 0.2)';
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.arc(centerX, centerY - 100, 100, 0, Math.PI, true);
    ctx.stroke();
    ctx.setLineDash([]);

    const indicatorAngle = (horizontalAngle * Math.PI) / 180 - Math.PI / 2;
    const indicatorRadius = 80;
    const indicatorX = centerX + Math.cos(indicatorAngle) * indicatorRadius;
    const indicatorY = centerY - 100 + Math.sin(indicatorAngle) * indicatorRadius;

    ctx.beginPath();
    ctx.arc(indicatorX, indicatorY, 6, 0, Math.PI * 2);
    ctx.fillStyle = '#f59e0b';
    ctx.fill();
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2;
    ctx.stroke();

  }, [verticalAngle, horizontalAngle]);

  return (
    <div className="bg-slate-900/50 rounded-xl p-6 border border-slate-700">
      <canvas
        ref={canvasRef}
        width={400}
        height={400}
        className="w-full h-auto"
      />
    </div>
  );
}

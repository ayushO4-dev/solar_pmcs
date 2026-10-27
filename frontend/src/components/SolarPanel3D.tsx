import { useEffect, useRef } from 'react';

interface SolarPanel3DProps {
  verticalAngle: number;
  horizontalAngle: number;
}

interface Point3D {
  x: number;
  y: number;
  z: number;
}

interface Point2D {
  x: number;
  y: number;
}

export default function SolarPanel3D({ verticalAngle, horizontalAngle }: SolarPanel3DProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const project3D = (point: Point3D, cameraDistance: number = 800): Point2D => {
    const scale = cameraDistance / (cameraDistance + point.z);
    return {
      x: point.x * scale,
      y: point.y * scale
    };
  };

  const rotateX = (point: Point3D, angle: number): Point3D => {
    const rad = (angle * Math.PI) / 180;
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);
    return {
      x: point.x,
      y: point.y * cos - point.z * sin,
      z: point.y * sin + point.z * cos
    };
  };

  const rotateY = (point: Point3D, angle: number): Point3D => {
    const rad = (angle * Math.PI) / 180;
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);
    return {
      x: point.x * cos + point.z * sin,
      y: point.y,
      z: -point.x * sin + point.z * cos
    };
  };

  const rotateZ = (point: Point3D, angle: number): Point3D => {
    const rad = (angle * Math.PI) / 180;
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);
    return {
      x: point.x * cos - point.y * sin,
      y: point.x * sin + point.y * cos,
      z: point.z
    };
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const cameraDistance = 800;

    const drawCuboid = (width: number, height: number, depth: number, x: number, y: number, z: number, color: string) => {
      const hw = width / 2;
      const hh = height / 2;
      const hd = depth / 2;

      const vertices: Point3D[] = [
        { x: -hw + x, y: -hh + y, z: -hd + z },
        { x: hw + x, y: -hh + y, z: -hd + z },
        { x: hw + x, y: hh + y, z: -hd + z },
        { x: -hw + x, y: hh + y, z: -hd + z },
        { x: -hw + x, y: -hh + y, z: hd + z },
        { x: hw + x, y: -hh + y, z: hd + z },
        { x: hw + x, y: hh + y, z: hd + z },
        { x: -hw + x, y: hh + y, z: hd + z }
      ];

      const rotated = vertices.map(v => rotateZ(rotateY(rotateX(v, verticalAngle), horizontalAngle), 0));
      const projected = rotated.map(p => project3D(p, cameraDistance));

      const faces = [
        [0, 1, 5, 4],
        [1, 2, 6, 5],
        [2, 3, 7, 6],
        [3, 0, 4, 7],
        [4, 5, 6, 7],
        [0, 1, 2, 3]
      ];

      faces.forEach((face) => {
        const avgZ = face.reduce((sum, idx) => sum + rotated[idx].z, 0) / face.length;

        ctx.beginPath();
        ctx.moveTo(centerX + projected[face[0]].x, centerY + projected[face[0]].y);
        face.slice(1).forEach(idx => {
          ctx.lineTo(centerX + projected[idx].x, centerY + projected[idx].y);
        });
        ctx.closePath();

        const brightness = Math.max(0.3, 1 - Math.abs(avgZ) / 250);
        const rgb = parseInt(color.slice(1), 16);
        const r = Math.floor((rgb >> 16) * brightness);
        const g = Math.floor(((rgb >> 8) & 255) * brightness);
        const b = Math.floor((rgb & 255) * brightness);

        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fill();
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });
    };

    drawCuboid(80, 40, 80, 0, -20, 0, '#8b7355');

    drawCuboid(15, 100, 20, -20, 30, 40, '#4a4a4a');
    drawCuboid(15, 100, 20, 20, 30, 40, '#4a4a4a');

    const panelVertices: Point3D[] = [
      { x: -80, y: 80, z: 40 },
      { x: 80, y: 80, z: 40 },
      { x: 80, y: 100, z: 40 },
      { x: -80, y: 100, z: 40 },
      { x: -80, y: 80, z: 120 },
      { x: 80, y: 80, z: 120 },
      { x: 80, y: 100, z: 120 },
      { x: -80, y: 100, z: 120 }
    ];

    const rotatedPanelVertices = panelVertices.map(v => {
      let rotated = v;
      rotated = rotateZ(rotated, verticalAngle);
      rotated = rotateY(rotated, horizontalAngle);
      return rotated;
    });

    const projectedPanel = rotatedPanelVertices.map(p => project3D(p, cameraDistance));

    const panelFaces = [
      [0, 1, 5, 4],
      [1, 2, 6, 5],
      [2, 3, 7, 6],
      [3, 0, 4, 7],
      [4, 5, 6, 7],
      [0, 1, 2, 3]
    ];

    panelFaces.forEach(face => {
      const avgZ = face.reduce((sum, idx) => sum + rotatedPanelVertices[idx].z, 0) / face.length;
      const panelColor = '#1e40af';
      const brightness = Math.max(0.4, 1 - Math.abs(avgZ) / 250);
      const rgb = parseInt(panelColor.slice(1), 16);
      const r = Math.floor((rgb >> 16) * brightness);
      const g = Math.floor(((rgb >> 8) & 255) * brightness);
      const b = Math.floor((rgb & 255) * brightness);

      ctx.beginPath();
      ctx.moveTo(centerX + projectedPanel[face[0]].x, centerY + projectedPanel[face[0]].y);
      face.slice(1).forEach(idx => {
        ctx.lineTo(centerX + projectedPanel[idx].x, centerY + projectedPanel[idx].y);
      });
      ctx.closePath();

      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fill();
      ctx.strokeStyle = '#0f172a';
      ctx.lineWidth = 2;
      ctx.stroke();
    });

    ctx.fillStyle = '#333';
    ctx.font = 'bold 13px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText(`Roll: ${verticalAngle.toFixed(0)}°`, centerX, 25);
    ctx.fillText(`Yaw: ${horizontalAngle.toFixed(0)}°`, centerX, 45);

  }, [verticalAngle, horizontalAngle]);

  return (
    <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
      <canvas
        ref={canvasRef}
        width={450}
        height={400}
        className="w-full h-auto border border-gray-200 rounded bg-gray-50"
      />
    </div>
  );
}

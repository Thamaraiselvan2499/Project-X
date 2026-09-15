import { useEffect, useRef } from "react";

const SEVERITY_COLORS = {
  minor: "#2f9e44",
  moderate: "#f08c00",
  severe: "#e03131",
};

export default function AnnotatedImage({ imageUrl, detections, imageWidth, imageHeight }) {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);

  useEffect(() => {
    draw();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [imageUrl, detections]);

  function draw() {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img || !imageWidth || !imageHeight) return;

    const scale = canvas.width / imageWidth;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    detections.forEach((det) => {
      const color = SEVERITY_COLORS[det.severity] ?? "#1971c2";
      const { x_min, y_min, x_max, y_max } = det.bbox;
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(x_min * scale, y_min * scale, (x_max - x_min) * scale, (y_max - y_min) * scale);

      const label = `${det.damage_type} · ${det.severity}${det.needs_review ? " ⚠" : ""}`;
      ctx.font = "13px sans-serif";
      const textWidth = ctx.measureText(label).width;
      ctx.fillStyle = color;
      ctx.fillRect(x_min * scale, Math.max(0, y_min * scale - 18), textWidth + 8, 18);
      ctx.fillStyle = "#fff";
      ctx.fillText(label, x_min * scale + 4, Math.max(12, y_min * scale - 5));
    });
  }

  const displayWidth = 640;
  const displayHeight = imageWidth && imageHeight ? (displayWidth * imageHeight) / imageWidth : 480;

  return (
    <div className="annotated-image">
      {/* Hidden source image used only to draw pixels onto the canvas */}
      <img
        ref={imgRef}
        src={imageUrl}
        alt="uploaded car"
        style={{ display: "none" }}
        onLoad={draw}
      />
      <canvas ref={canvasRef} width={displayWidth} height={displayHeight} />
    </div>
  );
}

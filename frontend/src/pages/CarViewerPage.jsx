import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import { createCar } from "../car3d/buildCar.js";

const DEFAULT_COLOR = 0xffffff;
const HOVER_COLOR = 0xffd43b;
const SELECTED_COLOR = 0xfa5252;

function titleCase(s) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function CarViewerPage({ bodyType, selectedParts, onTogglePart, onContinue }) {
  const mountRef = useRef(null);
  const stateRef = useRef({});
  const [hoveredPart, setHoveredPart] = useState(null);
  const [tooltipPos, setTooltipPos] = useState(null);

  // Selection is driven from React state (selectedParts), but the click
  // handler lives inside a three.js render loop set up once — read the
  // latest value through a ref instead of re-running the whole three.js
  // setup effect every time the selection changes.
  const selectedPartsRef = useRef(selectedParts);
  selectedPartsRef.current = selectedParts;

  function onToggle(part) {
    onTogglePart(part);
  }

  useEffect(() => {
    const mount = mountRef.current;
    const width = mount.clientWidth;
    const height = 420;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeef1f5);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(5, 3, 5);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.minDistance = 3;
    controls.maxDistance = 12;
    controls.maxPolarAngle = Math.PI / 2.05; // don't let the camera go below the ground

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(4, 8, 4);
    scene.add(dirLight);

    const ground = new THREE.Mesh(
      new THREE.CircleGeometry(6, 32),
      new THREE.MeshStandardMaterial({ color: 0xd8dee6 })
    );
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);

    const { group: carGroup, hotspots } = createCar(bodyType);
    scene.add(carGroup);

    const hotspotMeshes = hotspots.map(({ part, position }) => {
      const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.09, 16, 16),
        new THREE.MeshStandardMaterial({ color: DEFAULT_COLOR })
      );
      mesh.position.copy(position);
      mesh.userData.part = part;
      scene.add(mesh);
      return mesh;
    });

    function colorFor(part, isHovered) {
      if (selectedPartsRef.current.includes(part)) return SELECTED_COLOR;
      if (isHovered) return HOVER_COLOR;
      return DEFAULT_COLOR;
    }

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let hovered = null;

    function pointerToNDC(event) {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }

    function handlePointerMove(event) {
      pointerToNDC(event);
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(hotspotMeshes);
      const next = hits.length > 0 ? hits[0].object : null;

      if (next !== hovered) {
        if (hovered) hovered.material.color.setHex(colorFor(hovered.userData.part, false));
        if (next) next.material.color.setHex(colorFor(next.userData.part, true));
        hovered = next;
        setHoveredPart(next ? next.userData.part : null);
      }
      setTooltipPos(next ? { x: event.clientX, y: event.clientY } : null);
      renderer.domElement.style.cursor = next ? "pointer" : "grab";
    }

    function handleClick(event) {
      pointerToNDC(event);
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(hotspotMeshes);
      if (hits.length > 0) {
        onToggle(hits[0].object.userData.part);
      }
    }

    renderer.domElement.addEventListener("pointermove", handlePointerMove);
    renderer.domElement.addEventListener("click", handleClick);

    function handleResize() {
      const w = mount.clientWidth;
      camera.aspect = w / height;
      camera.updateProjectionMatrix();
      renderer.setSize(w, height);
    }
    window.addEventListener("resize", handleResize);

    let frameId;
    function animate() {
      // Re-apply colors every frame from the latest selection ref, so
      // toggling a part from the checklist below (not just a 3D click)
      // is reflected without re-running this whole effect.
      hotspotMeshes.forEach((mesh) => {
        const isHovered = mesh === hovered;
        mesh.material.color.setHex(colorFor(mesh.userData.part, isHovered));
      });
      controls.update();
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    }
    animate();

    stateRef.current = { renderer, mount };

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("pointermove", handlePointerMove);
      renderer.domElement.removeEventListener("click", handleClick);
      controls.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bodyType]);

  return (
    <div className="card">
      <h2>Where's the damage?</h2>
      <p className="muted">
        Drag to rotate the model, scroll to zoom, and click a marker on the part that's damaged. This is a
        schematic diagram (not a photo of your exact car) — it's only for pointing out location.
      </p>
      <div className="car-viewer-canvas" ref={mountRef}>
        {tooltipPos && hoveredPart && (
          <div className="car-viewer-tooltip" style={{ left: tooltipPos.x + 12, top: tooltipPos.y + 12 }}>
            {titleCase(hoveredPart)}
          </div>
        )}
      </div>

      <div className="part-checklist">
        {[...selectedParts].length === 0 && <p className="muted">No parts selected yet.</p>}
        {selectedParts.map((part) => (
          <span className="part-chip" key={part}>
            {titleCase(part)}
            <button type="button" onClick={() => onToggle(part)} aria-label={`Remove ${part}`}>
              ×
            </button>
          </span>
        ))}
      </div>

      <button type="button" disabled={selectedParts.length === 0} onClick={onContinue}>
        Upload photos for {selectedParts.length} part{selectedParts.length === 1 ? "" : "s"}
      </button>
    </div>
  );
}

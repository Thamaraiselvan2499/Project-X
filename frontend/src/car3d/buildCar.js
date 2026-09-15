import * as THREE from "three";

// Schematic (not photorealistic) parametric car body per body type. Built
// from primitives rather than a licensed/downloaded 3D model — see
// CarViewerPage's note to the user about what this is and isn't.
const DIMENSIONS = {
  hatchback: { length: 3.9, width: 1.7, height: 1.45, cabinLength: 1.9, cabinOffset: -0.15 },
  sedan: { length: 4.6, width: 1.75, height: 1.4, cabinLength: 1.9, cabinOffset: -0.25 },
  suv: { length: 4.4, width: 1.85, height: 1.8, cabinLength: 2.1, cabinOffset: -0.1 },
};

// Declarative hotspot layout in normalized coordinates:
//   u: -1 (rear) .. +1 (front) along the car's length
//   v: -1 (right) .. +1 (left) across the car's width
//   h: a named height band, resolved against the actual body dimensions
// One entry per part_labels entry from ml/configs/damage_classes.yaml.
const HOTSPOT_LAYOUT = [
  { part: "front_bumper", u: 0.97, v: 0, h: "low" },
  { part: "rear_bumper", u: -0.97, v: 0, h: "low" },
  { part: "grille", u: 0.99, v: 0, h: "mid" },
  { part: "bonnet", u: 0.55, v: 0, h: "hood" },
  { part: "boot_lid", u: -0.55, v: 0, h: "hood" },
  { part: "roof", u: 0, v: 0, h: "roof" },
  { part: "left_headlight", u: 0.9, v: 0.85, h: "mid" },
  { part: "right_headlight", u: 0.9, v: -0.85, h: "mid" },
  { part: "left_tail_light", u: -0.9, v: 0.85, h: "mid" },
  { part: "right_tail_light", u: -0.9, v: -0.85, h: "mid" },
  { part: "left_front_fender", u: 0.5, v: 1.0, h: "mid" },
  { part: "right_front_fender", u: 0.5, v: -1.0, h: "mid" },
  { part: "left_quarter_panel", u: -0.5, v: 1.0, h: "mid" },
  { part: "right_quarter_panel", u: -0.5, v: -1.0, h: "mid" },
  { part: "left_front_door", u: 0.15, v: 1.0, h: "cabin" },
  { part: "right_front_door", u: 0.15, v: -1.0, h: "cabin" },
  { part: "left_rear_door", u: -0.2, v: 1.0, h: "cabin" },
  { part: "right_rear_door", u: -0.2, v: -1.0, h: "cabin" },
  { part: "left_side_mirror", u: 0.35, v: 1.08, h: "cabin_top" },
  { part: "right_side_mirror", u: 0.35, v: -1.08, h: "cabin_top" },
  { part: "front_windshield", u: 0.38, v: 0, h: "windshield" },
  { part: "rear_windshield", u: -0.38, v: 0, h: "windshield" },
];

export function createCar(bodyType) {
  const dims = DIMENSIONS[bodyType] || DIMENSIONS.hatchback;
  const wheelRadius = 0.32;
  const wheelWidth = 0.22;
  const groundClearance = wheelRadius;
  const chassisHeight = dims.height * 0.5;
  const cabinHeight = dims.height - chassisHeight;
  const cabinWidth = dims.width * 0.85;

  const group = new THREE.Group();

  const chassis = new THREE.Mesh(
    new THREE.BoxGeometry(dims.length, chassisHeight, dims.width),
    new THREE.MeshStandardMaterial({ color: 0xc0392b })
  );
  chassis.position.y = groundClearance + chassisHeight / 2;
  group.add(chassis);

  const cabin = new THREE.Mesh(
    new THREE.BoxGeometry(dims.cabinLength, cabinHeight, cabinWidth),
    new THREE.MeshStandardMaterial({ color: 0x2c3e50 })
  );
  cabin.position.set(dims.cabinOffset, groundClearance + chassisHeight + cabinHeight / 2, 0);
  group.add(cabin);

  const wheelGeo = new THREE.CylinderGeometry(wheelRadius, wheelRadius, wheelWidth, 20);
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
  const wheelX = dims.length / 2 - wheelRadius * 1.3;
  const wheelZ = dims.width / 2 + wheelWidth * 0.05;
  for (const sx of [1, -1]) {
    for (const sz of [1, -1]) {
      const wheel = new THREE.Mesh(wheelGeo, wheelMat);
      wheel.rotation.x = Math.PI / 2;
      wheel.position.set(sx * wheelX, wheelRadius, sz * wheelZ);
      group.add(wheel);
    }
  }

  const bumperMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a });
  const bumperGeo = new THREE.BoxGeometry(0.18, chassisHeight * 0.55, dims.width * 0.95);
  const frontBumper = new THREE.Mesh(bumperGeo, bumperMat);
  frontBumper.position.set(dims.length / 2 - 0.09, groundClearance + chassisHeight * 0.35, 0);
  group.add(frontBumper);
  const rearBumper = frontBumper.clone();
  rearBumper.position.x = -(dims.length / 2 - 0.09);
  group.add(rearBumper);

  const heightBand = (h) => {
    switch (h) {
      case "low":
        return groundClearance + chassisHeight * 0.3;
      case "hood":
        return groundClearance + chassisHeight + 0.02;
      case "roof":
        return groundClearance + chassisHeight + cabinHeight + 0.02;
      case "cabin":
        return groundClearance + chassisHeight + cabinHeight * 0.5;
      case "cabin_top":
        return groundClearance + chassisHeight + cabinHeight * 0.9;
      case "windshield":
        return groundClearance + chassisHeight + cabinHeight * 0.8;
      case "mid":
      default:
        return groundClearance + chassisHeight * 0.75;
    }
  };

  const cabinRelated = new Set(["cabin", "cabin_top", "windshield", "roof"]);
  const hotspots = HOTSPOT_LAYOUT.map(({ part, u, v, h }) => {
    const halfWidth = (cabinRelated.has(h) ? cabinWidth : dims.width) / 2;
    return {
      part,
      position: new THREE.Vector3(u * (dims.length / 2), heightBand(h), v * halfWidth),
    };
  });

  return { group, hotspots, dims };
}

export const SUPPORTED_BODY_TYPES = Object.keys(DIMENSIONS);

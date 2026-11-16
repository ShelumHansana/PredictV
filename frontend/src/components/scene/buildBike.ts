// A motorbike drawn from simple 3D shapes, in the style of a technical line drawing.
// Solid faces are painted in the page colour so lines behind them are hidden.
import * as THREE from "three";

export interface BikeColors { paper: string; ink: string; accent: string; faint: string }
export interface BikeModel {
  bike: THREE.Group;
  wheels: THREE.Group[];
  setColors: (c: BikeColors) => void;
  dispose: () => void;
}

const UP = new THREE.Vector3(0, 1, 0);
type P = [number, number, number];

export function buildBike(): BikeModel {
  const bike = new THREE.Group();
  const solid = new THREE.MeshBasicMaterial({ polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
  const ink = new THREE.LineBasicMaterial();
  const accent = new THREE.LineBasicMaterial();
  const faint = new THREE.LineBasicMaterial();
  const geometries: THREE.BufferGeometry[] = [];

  const part = (geometry: THREE.BufferGeometry, lines: THREE.LineBasicMaterial = ink, parent: THREE.Object3D = bike) => {
    const edges = new THREE.EdgesGeometry(geometry, 18);
    geometries.push(geometry, edges);
    const mesh = new THREE.Mesh(geometry, solid);
    mesh.add(new THREE.LineSegments(edges, lines));
    parent.add(mesh);
    return mesh;
  };
  /** A straight tube from a to b. */
  const tube = (a: P, b: P, radius = 0.05, lines: THREE.LineBasicMaterial = ink) => {
    const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b);
    const mesh = part(new THREE.CylinderGeometry(radius, radius, A.distanceTo(B), 8), lines);
    mesh.position.copy(A).add(B).multiplyScalar(0.5);
    mesh.quaternion.setFromUnitVectors(UP, B.clone().sub(A).normalize());
    return mesh;
  };
  const bothSides = (fn: (side: number) => void) => [-1, 1].forEach(fn);

  // wheels
  const wheel = (x: number) => {
    const w = new THREE.Group();
    part(new THREE.TorusGeometry(0.95, 0.17, 8, 48), ink, w);
    part(new THREE.TorusGeometry(0.74, 0.03, 6, 48), faint, w);
    part(new THREE.CylinderGeometry(0.13, 0.13, 0.34, 10), accent, w).rotation.x = Math.PI / 2;
    const points: number[] = [];
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      points.push(0.12 * Math.cos(a), 0.12 * Math.sin(a), 0, 0.74 * Math.cos(a + 0.25), 0.74 * Math.sin(a + 0.25), 0);
    }
    const spokes = new THREE.BufferGeometry();
    spokes.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
    geometries.push(spokes);
    w.add(new THREE.LineSegments(spokes, faint));
    const disc = part(new THREE.CylinderGeometry(0.34, 0.34, 0.03, 20), faint, w);
    disc.rotation.x = Math.PI / 2;
    disc.position.z = 0.14;
    w.position.set(x, 0, 0);
    bike.add(w);
    return w;
  };
  const rear = wheel(-1.8), front = wheel(1.9);

  // frame
  const head: P = [1.02, 1.78, 0];
  tube(head, [0.6, 0.02, 0], 0.06);
  tube(head, [-0.45, 1.3, 0], 0.07);
  tube([-0.45, 1.3, 0], [-2.15, 1.5, 0], 0.05);
  tube([-2.15, 1.5, 0], [-0.62, 0.4, 0], 0.04, faint);
  tube([0.6, 0.02, 0], [-0.62, 0.02, 0], 0.05);
  tube([-0.62, 0.02, 0], [-0.62, 1.25, 0], 0.05);
  bothSides(s => {
    tube([-0.62, 0.22, 0.2 * s], [-1.8, 0, 0.2 * s], 0.05);
    tube([-1.25, 0.2, 0.26 * s], [-1.05, 1.32, 0.26 * s], 0.06, accent);
    tube([1.9, 0, 0.19 * s], [0.98, 1.95, 0.19 * s], 0.065);
    tube([0.9, 2.02, 0.62 * s], [0.78, 2.0, 0.86 * s], 0.055, accent);
  });
  tube([0.9, 2.02, -0.62], [0.9, 2.02, 0.62], 0.04);

  // engine
  part(new THREE.BoxGeometry(0.95, 0.62, 0.56)).position.set(0, 0.36, 0);
  const barrel = part(new THREE.CylinderGeometry(0.24, 0.26, 0.62, 10), accent);
  barrel.position.set(0.22, 0.95, 0);
  barrel.rotation.z = -0.3;
  for (let i = 0; i < 4; i++) {
    const fin = part(new THREE.CylinderGeometry(0.33, 0.33, 0.02, 14), faint);
    fin.position.set(0.16 + i * 0.045, 0.78 + i * 0.13, 0);
    fin.rotation.z = -0.3;
  }
  const cover = part(new THREE.CylinderGeometry(0.27, 0.27, 0.06, 16), faint);
  cover.rotation.x = Math.PI / 2;
  cover.position.set(-0.12, 0.36, 0.31);

  // tank, seat, lights, mudguards
  const tank = part(new THREE.SphereGeometry(0.5, 14, 8));
  tank.scale.set(1.55, 0.72, 0.78);
  tank.position.set(0.22, 1.56, 0);
  const seat = part(new THREE.BoxGeometry(1.55, 0.2, 0.52));
  seat.position.set(-1.2, 1.56, 0);
  seat.rotation.z = -0.07;
  part(new THREE.SphereGeometry(0.24, 12, 8), accent).position.set(1.34, 1.66, 0);
  part(new THREE.BoxGeometry(0.12, 0.14, 0.3), accent).position.set(-2.22, 1.5, 0);
  const frontGuard = part(new THREE.TorusGeometry(1.2, 0.035, 6, 24, Math.PI * 0.55), faint);
  frontGuard.position.set(1.9, 0, 0);
  frontGuard.rotation.z = Math.PI * 0.32;
  const rearGuard = part(new THREE.TorusGeometry(1.2, 0.035, 6, 24, Math.PI * 0.45), faint);
  rearGuard.position.set(-1.8, 0, 0);
  rearGuard.rotation.z = Math.PI * 0.42;

  // exhaust
  tube([0.36, 0.86, 0.22], [0.5, 0.1, 0.34], 0.055);
  tube([0.5, 0.1, 0.34], [-0.7, -0.06, 0.36], 0.055);
  tube([-0.7, -0.06, 0.36], [-2.25, 0.36, 0.4], 0.14, accent);

  bike.children.forEach(child => { child.position.y -= 0.85; });   // centre on its own origin

  return {
    bike,
    wheels: [rear, front],
    setColors(c) {
      solid.color.set(c.paper);
      ink.color.set(c.ink);
      accent.color.set(c.accent);
      faint.color.set(c.faint);
    },
    dispose() {
      geometries.forEach(g => g.dispose());
      [solid, ink, accent, faint].forEach(m => m.dispose());
    },
  };
}

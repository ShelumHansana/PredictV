import { useEffect, useRef } from "react";
import * as THREE from "three";
import { buildBike, type BikeColors } from "./buildBike";

interface Props {
  /** Extra quarter-turns, e.g. the wizard step. */
  turn?: number;
}

const START_ANGLE = -0.55;

function readColors(): BikeColors {
  const css = getComputedStyle(document.documentElement);
  const v = (name: string) => css.getPropertyValue(name).trim();
  return { paper: v("--surface"), ink: v("--ink"), accent: v("--accent"), faint: v("--ink-3") };
}

/** The 3D bike. It turns as the page scrolls, leans toward the pointer, and follows the theme colours. */
export default function BikeCanvas({ turn = 0 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const turnRef = useRef(turn);
  turnRef.current = turn;

  useEffect(() => {
    const canvas = canvasRef.current;
    const box = canvas?.parentElement;
    if (!canvas || !box) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    } catch {
      return;   // no WebGL: the figure box just stays empty
    }
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
    camera.position.set(0, 0, 12);
    const model = buildBike();
    model.setColors(readColors());
    const rig = new THREE.Group();
    rig.add(model.bike);
    rig.rotation.x = 0.12;
    scene.add(rig);

    let angle = START_ANGLE, tilt = 0, pointerX = 0, pointerY = 0, raf = 0, running = true;

    const resize = () => {
      const w = box.clientWidth, h = box.clientHeight;
      if (!w || !h) return;
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      // fit the bike (about 5.4 x 3.4 units, wider when turned) inside the box
      const worldH = 2 * Math.tan((camera.fov * Math.PI) / 360) * camera.position.z;
      rig.scale.setScalar(Math.min((worldH * camera.aspect) / 6.4, worldH / 4.2));
    };

    const draw = (time: number) => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const progress = max > 0 ? Math.min(1, window.scrollY / max) : 0;
      // kept under ~60 degrees so the bike is never seen edge-on
      const target = START_ANGLE + progress * 0.9 + turnRef.current * 0.35 + pointerX * 0.25;
      if (reduce) { angle = target; tilt = 0; }
      else { angle += (target - angle) * 0.07; tilt += (pointerY * 0.1 - tilt) * 0.07; }
      model.bike.rotation.y = angle;
      model.bike.rotation.x = tilt;
      model.bike.position.y = reduce ? 0 : Math.sin(time / 1500) * 0.05;
      const spin = -(window.scrollY * 0.012) - (reduce ? 0 : time / 2800);
      model.wheels.forEach(w => { w.rotation.z = spin; });
      renderer.render(scene, camera);
    };
    const loop = (time: number) => { draw(time); if (running) raf = requestAnimationFrame(loop); };
    const drawOnce = () => draw(0);

    const onPointer = (e: PointerEvent) => { pointerX = e.clientX / window.innerWidth - 0.5; pointerY = e.clientY / window.innerHeight - 0.5; };
    const onVisibility = () => {
      running = !document.hidden;
      if (running && !reduce) raf = requestAnimationFrame(loop);
    };
    const sizeWatcher = new ResizeObserver(() => { resize(); if (reduce) drawOnce(); });
    const themeWatcher = new MutationObserver(() => { model.setColors(readColors()); if (reduce) drawOnce(); });

    resize();
    sizeWatcher.observe(box);
    themeWatcher.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    if (reduce) {
      window.addEventListener("scroll", drawOnce, { passive: true });
      drawOnce();
    } else {
      window.addEventListener("pointermove", onPointer, { passive: true });
      document.addEventListener("visibilitychange", onVisibility);
      raf = requestAnimationFrame(loop);
    }

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      sizeWatcher.disconnect();
      themeWatcher.disconnect();
      window.removeEventListener("scroll", drawOnce);
      window.removeEventListener("pointermove", onPointer);
      document.removeEventListener("visibilitychange", onVisibility);
      model.dispose();
      renderer.dispose();
    };
  }, []);

  return <canvas ref={canvasRef} aria-hidden="true" />;
}

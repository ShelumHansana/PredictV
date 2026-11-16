import { useEffect, useRef, useState } from "react";
import "./scene.css";

interface Props { caption: string; number: string; turn?: number; className?: string }

const views = [
  { src: "/showcase/street-bike.webp", label: "Three-quarter motorcycle view" },
  { src: "/showcase/rear-angle.webp", label: "Rear motorcycle view" },
  { src: "/showcase/front-angle.webp", label: "Front motorcycle view" },
];

/** Immersive 2.5D motorcycle showcase with real slide controls. No network services required. */
export function BikeFigure({ caption, number, turn = 0, className = "" }: Props) {
  const [active, setActive] = useState(0);
  const [motion, setMotion] = useState({ x: 0, y: 0 });
  const [paused, setPaused] = useState(false);
  const figure = useRef<HTMLDivElement>(null);

  useEffect(() => { setActive(turn % views.length); }, [turn]);
  useEffect(() => {
    if (paused || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = window.setInterval(() => setActive(n => (n + 1) % views.length), 8500);
    return () => window.clearInterval(id);
  }, [paused]);

  function pointerMove(e: React.PointerEvent<HTMLDivElement>) {
    if (e.pointerType === "touch" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setMotion({ x: x * 8, y: y * -7 });
  }

  const rotate = (direction: number) => setActive(n => (n + direction + views.length) % views.length);
  return (
    <div ref={figure} className={`figure showcase ${className}`} onPointerMove={pointerMove}
      onPointerLeave={() => { setMotion({ x: 0, y: 0 }); setPaused(false); }}
      onPointerEnter={() => setPaused(true)}
      onFocusCapture={() => setPaused(true)} onBlurCapture={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setPaused(false); }}
      role="group" aria-roledescription="carousel" aria-label="Motorcycle showcase">
      <div className="showcase__ambient" aria-hidden="true" />
      <div className="showcase__grid" aria-hidden="true" />
      <div className="showcase__hud" aria-hidden="true"><span>PV / MOTION LAB</span><span className="showcase__live">3D EXPERIENCE</span></div>
      <div className="showcase__preview-row" aria-label="Motorcycle viewing angles">
        {[1, 2].map(i => (
          <button key={i} type="button" className={`showcase__preview ${active === i ? "is-active" : ""}`}
            onClick={() => setActive(i)} aria-label={`Show ${views[i].label}`} aria-pressed={active === i}>
            <img src={views[i].src} alt="" loading="lazy" draggable={false} />
            <span>{i === 1 ? "REAR / 03" : "FRONT / 02"}</span>
          </button>
        ))}
      </div>
      <div className="showcase__stage" style={{ transform: `perspective(1000px) rotateY(${motion.x}deg) rotateX(${motion.y}deg)` }}>
        <div className="showcase__halo" aria-hidden="true" />
        {views.map((view, i) => (
          <img key={view.src} src={view.src} alt={i === active ? view.label : ""}
            aria-hidden={i !== active} draggable={false}
            className={`showcase__bike showcase__bike--${i} ${i === active ? "is-active" : ""}`}
            loading={i === 0 ? "eager" : "lazy"} />
        ))}
        <div className="showcase__platform" aria-hidden="true" />
      </div>
      <div className="showcase__bottom">
        <span className="figure__caption"><b>Fig. {number}</b> — {caption}</span>
        <div className="showcase__controls" aria-label="Change motorcycle view">
          <button className="showcase__arrow" type="button" onClick={() => rotate(-1)} aria-label="Previous motorcycle view">‹</button>
          <div className="showcase__dots">{views.map((view, i) => <button key={view.src} type="button"
            className={active === i ? "is-active" : ""} onClick={() => setActive(i)}
            aria-label={`Show view ${i + 1}: ${view.label}`} aria-current={active === i ? "true" : undefined} />)}</div>
          <button className="showcase__arrow" type="button" onClick={() => rotate(1)} aria-label="Next motorcycle view">›</button>
        </div>
      </div>
    </div>
  );
}

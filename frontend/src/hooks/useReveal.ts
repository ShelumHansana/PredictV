import { useEffect, useRef } from "react";

/** Adds the class "in" the first time the element scrolls into view (see .reveal in global.css). */
export function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.classList.add("in");
      return;
    }
    const io = new IntersectionObserver(entries => {
      if (entries.some(e => e.isIntersecting)) { el.classList.add("in"); io.disconnect(); }
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.05 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return ref;
}

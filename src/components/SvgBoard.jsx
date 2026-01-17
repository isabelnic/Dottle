import { useEffect, useState } from "react";

export default function SvgBoard({ src, revealOutline }) {
  const [svgText, setSvgText] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setSvgText("");
      const res = await fetch(src);
      if (!res.ok) throw new Error(`Failed to load SVG: ${src}`);
      const text = await res.text();
      if (!cancelled) setSvgText(text);
    }

    load().catch((e) => {
      console.error(e);
      if (!cancelled) setSvgText(`<svg xmlns="http://www.w3.org/2000/svg"></svg>`);
    });

    return () => {
      cancelled = true;
    };
  }, [src]);

  return (
    <div className={`board ${revealOutline ? "reveal-outline" : ""}`}>
      <div className="svg-wrap" dangerouslySetInnerHTML={{ __html: svgText }} />
    </div>
  );
}
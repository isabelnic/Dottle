import { useEffect, useMemo, useRef, useState } from "react";

export default function CountryAutocomplete({ options, value, onChange, onPick, disabled = false, placeholder = "Guess the country…" }) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const wrapRef = useRef(null);

  const filtered = useMemo(() => {
    const q = value.trim().toLowerCase();
    if (!q) return [];
    return options
      .filter((o) => o.toLowerCase().startsWith(q))
      .slice(0, 8);
  }, [options, value]);

  useEffect(() => {
    setOpen(filtered.length > 0);
    setActiveIndex(-1);
  }, [filtered.length]);

  useEffect(() => {
    const onDocClick = (e) => {
      if (!wrapRef.current) return;
      if (!wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const pick = (name) => {
    onPick(name);
    setOpen(false);
  };

  const onKeyDown = (e) => {
    if (!open || filtered.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      if (activeIndex >= 0) {
        e.preventDefault();
        pick(filtered[activeIndex]);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={wrapRef} style={{ position: "relative", flex: 1 }}>
      <input
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setOpen(filtered.length > 0)}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
        style={{ padding: 10, width: "100%", borderRadius: 8, border: "1px solid #ddd" }}
        autoComplete="off"
      />

      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            right: 0,
            background: "white",
            border: "1px solid #e6e6e6",
            borderRadius: 10,
            overflow: "hidden",
            boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
            zIndex: 10,
          }}
        >
          {filtered.map((name, idx) => (
            <div
              key={name}
              onMouseDown={() => pick(name)} // mousedown so it selects before blur
              style={{
                padding: "10px 12px",
                cursor: "pointer",
                background: idx === activeIndex ? "#f4f4f4" : "white",
              }}
            >
              {name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
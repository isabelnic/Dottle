import { useEffect, useMemo, useState } from "react";
import SvgBoard from "./components/SvgBoard";
import CountryAutocomplete from "./components/CountryAutocomplete";
import HintsPanel from "./components/HintsPanel";


const MAX_WRONG_BEFORE_POPULATIONS = 2;
const MAX_WRONG_BEFORE_EVAVATION = 4;
const MAX_WRONG_BEFORE_OUTLINE = 6;
const MAX_WRONG_BEFORE_CITY_3 = 8;
const MAX_WRONG_BEFORE_CITY_2 = 9;
const MAX_WRONG_BEFORE_CITY_1 = 10;
const MAX_WRONG_BEFORE_FLAG = 11;
const MAX_WRONG = 12;



export default function App() {
  const [manifest, setManifest] = useState([]);
  const [current, setCurrent] = useState(null);

  const [guess, setGuess] = useState("");
  const [wrongCount, setWrongCount] = useState(0);
  const [message, setMessage] = useState("");
  const [isRevealed, setIsRevealed] = useState(false);

  const revealCity3 = wrongCount >= MAX_WRONG_BEFORE_CITY_3;
  const revealCity2 = wrongCount >= MAX_WRONG_BEFORE_CITY_2;
  const revealCity1 = wrongCount >= MAX_WRONG_BEFORE_CITY_1;

  const revealFlag = wrongCount >= MAX_WRONG_BEFORE_FLAG;
  const hasFailed = wrongCount >= MAX_WRONG;
  const revealOutline = wrongCount >= MAX_WRONG_BEFORE_OUTLINE;

  const countryOptions = useMemo(() => {
    return manifest
      .map((m) => m.answer)
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b));
  }, [manifest]);

  useEffect(() => {
    async function loadManifest() {
      const res = await fetch("/svgs/manifest.json");
      if (!res.ok) throw new Error("Failed to load manifest.json");
      const data = await res.json();
      setManifest(data);
    }
    loadManifest().catch(console.error);
  }, []);

  const pickRandom = () => {
    if (manifest.length === 0) return;
    const next = manifest[Math.floor(Math.random() * manifest.length)];
    setIsRevealed(false);
    setCurrent(next);
    setGuess("");
    setWrongCount(0);
    setMessage("");
  };

  useEffect(() => {
    if (manifest.length > 0 && !current) pickRandom();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [manifest]);


  const svgSrc = useMemo(() => {
    if (!current) return "";
    return `/svgs/${current.file}`;
  }, [current]);

  const norm = (s) =>
  s.toLowerCase().trim().replace(/\s+/g, " ");

  const submitGuess = (e) => {
    e.preventDefault();
    if (!current) return;

    const g = norm(guess);
    const a = norm(current.answer || "");

    if (!g) return;

    if (g === a) {
      setMessage("✅ Correct!");
      setTimeout(() => pickRandom(), 600);
    } else {
      const nextWrong = wrongCount + 1;
      setWrongCount(nextWrong);

      if (nextWrong >= MAX_WRONG) {
        setIsRevealed(true);
        setMessage(`❌ Out of guesses. The answer was: ${current.answer}`);
        return;
      }

      setMessage("❌ Wrong. Try again.");
    }
  };

  return (
    // this is the main app container
    <div style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ marginTop: 0 }}>Dottle</h1>

      {current && (
        <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
          {/* LEFT: board + inputs */}
          <div>
          <SvgBoard src={svgSrc} revealOutline={revealOutline} />

          <form
            onSubmit={submitGuess}
            style={{
              marginTop: 16,
              display: "flex",
              gap: 8,
              width: "100%",
              alignItems: "stretch",
            }}
          >
            <div style={{ flex: 1, minWidth: 0 }}>
              <CountryAutocomplete
                options={countryOptions}
                value={guess}
                onChange={setGuess}
                onPick={(name) => setGuess(name)}
                disabled={isRevealed}
              />
            </div>

            <button type="submit" disabled={isRevealed} style={{ padding: "10px 18px", whiteSpace: "nowrap" }}>
              Guess
            </button>

            <button type="button" onClick={pickRandom} style={{ padding: "10px 18px", whiteSpace: "nowrap" }}>
              Skip
            </button>
          </form>

          <div style={{ marginTop: 10 }}>
            <div>{message}</div>
            <div style={{ opacity: 0.7 }}>Wrong guesses: {wrongCount}</div>
          </div>
        </div>
        {/* RIGHT: all hints live here */}
        <div style={{ width: 320, maxWidth: "40vw" }}>
          <HintsPanel 
            country={current} 
            wrongCount={wrongCount} 
            revealCity1={revealCity1}
            revealCity2={revealCity2}
            revealCity3={revealCity3}
            revealFlag={revealFlag}
            hasFailed={hasFailed} 
          />
        </div>
      </div>
    )}

      {!current && <div>Loading…</div>}
    </div>
  );
}
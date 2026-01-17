// function fmtPop(n) {
//   if (typeof n !== "number") return "";
//   if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
//   if (n >= 1_000) return `${Math.round(n / 1_000)}k`;
//   return `${n}`;
// }

// function fmtElev(n) {
//   if (typeof n !== "number") return "";
//   return `${Math.round(n)} m`;
// }



// // move the hints box to the right of the main game area

// export default function HintsPanel({ wrongCount, country }) {
//   if (!country) return null; // if wrong guess

//   // ✅ hide the whole hints box until it's unlocked
//   if (wrongCount < 2) return null;

//   // sort cities by population descending
//   const citiesSorted = [...(current?.cities || [])]
//     .sort((a, b) => b.population - a.population);

//   // top 3 cities
//   const top3 = (country.topCities || []).slice(0, 3);
//   // top 3 populations
//   const top3Pops = top3
//     .map((c) => c.population)
//     .filter((p) => typeof p === "number" && p > 0);

//   // top 3 elevations
//   const top3Elevs = top3
//     .map((c) => c.dem)
//     .map(Number)
//     .filter((e) => Number.isFinite(e));

//   return (
//     <div style={{ marginTop: 12, padding: 12, border: "1px solid #eee", borderRadius: 10 }}>
//       <div style={{ fontWeight: 600, marginBottom: 6 }}>Hints</div>

//       {/* Populations */}
//       <div style={{ opacity: 0.75, marginBottom: 4 }}>
//         Top 3 city populations
//       </div>

//       {top3Pops.length > 0 ? (
//         <div style={{ fontSize: 18 }}>
//           {top3Pops.map(fmtPop).join(" · ")}
//         </div>
//       ) : (
//         <div style={{ opacity: 0.75 }}>Population data unavailable.</div>
//       )}

//       {/* Elevations (unlocked later) */}
//       {wrongCount >= 4 && (
//         <>
//           <div style={{ opacity: 0.75, marginTop: 12, marginBottom: 4 }}>
//             Top 3 city elevations
//           </div>

//           {top3Elevs.length > 0 ? (
//             <div style={{ fontSize: 18 }}>
//               {top3Elevs.map(fmtElev).join(" · ")}
//             </div>
//           ) : (
//             <div style={{ opacity: 0.75 }}>Elevation data unavailable.</div>
//           )}
//         </>
//       )}
//     </div>
//   );
// }





function fmtPop(n) {
  if (typeof n !== "number") return "";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}k`;
  return `${n}`;
}

function fmtElev(n) {
  if (typeof n !== "number") return "";
  return `${Math.round(n)} m`;
}

export default function HintsPanel({
  wrongCount,
  country,
  revealCity1,
  revealCity2,
  revealCity3,
  revealFlag,
  hasFailed,
}) {
  if (!country) return null;

  // Hide the whole hints box until unlocked
  if (wrongCount < 2) return null;

  // Be robust to different manifest shapes
  const cities =
    (Array.isArray(country.topCities) && country.topCities) ||
    (Array.isArray(country.cities) && country.cities) ||
    [];

  const citiesSorted = [...cities].sort(
    (a, b) => (b?.population || 0) - (a?.population || 0)
  );

  const top3 = citiesSorted.slice(0, 3);

  const top3Pops = top3
    .map((c) => c?.population)
    .filter((p) => typeof p === "number" && p > 0);

  const top3Elevs = top3
    .map((c) => Number(c?.dem))
    .filter((e) => Number.isFinite(e));

  const city3 = citiesSorted[2]?.name;
  const city2 = citiesSorted[1]?.name;
  const city1 = citiesSorted[0]?.name;

  return (
    <div style={{ marginTop: 12, padding: 12, border: "1px solid #eee", borderRadius: 10 }}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>Hints</div>

      {/* Populations (unlocked at 2 wrong guesses) */}
      <div style={{ opacity: 0.75, marginBottom: 4 }}>Top 3 city populations</div>
      {top3Pops.length > 0 ? (
        <div style={{ fontSize: 18 }}>{top3Pops.map(fmtPop).join(" · ")}</div>
      ) : (
        <div style={{ opacity: 0.75 }}>Population data unavailable.</div>
      )}

      {/* Elevations (unlocked at 4 wrong guesses) */}
      {wrongCount >= 4 && (
        <>
          <div style={{ opacity: 0.75, marginTop: 12, marginBottom: 4 }}>Top 3 city elevations</div>
          {top3Elevs.length > 0 ? (
            <div style={{ fontSize: 18 }}>{top3Elevs.map(fmtElev).join(" · ")}</div>
          ) : (
            <div style={{ opacity: 0.75 }}>Elevation data unavailable.</div>
          )}
        </>
      )}

      {/* City-name ladder (uses the booleans App.jsx already computes) */}
      {(revealCity3 || revealCity2 || revealCity1) && (
        <>
          <div style={{ opacity: 0.75, marginTop: 12, marginBottom: 4 }}>City names</div>
          <div style={{ fontSize: 16, lineHeight: 1.4 }}>
            {revealCity3 && <div>3rd most populated: {city3 || "Unavailable"}</div>}
            {revealCity2 && <div>2nd most populated: {city2 || "Unavailable"}</div>}
            {revealCity1 && <div>Most populated: {city1 || "Unavailable"}</div>}
          </div>
        </>
      )}

      {/* Flag (only if your manifest actually contains something usable) */}
      {revealFlag && (
        <>
          <div style={{ opacity: 0.75, marginTop: 12, marginBottom: 4 }}>Flag</div>
          {country.flagEmoji ? (
            <div style={{ fontSize: 28 }}>{country.flagEmoji}</div>
          ) : country.flagUrl ? (
            <img src={country.flagUrl} alt="Flag" style={{ width: "100%", borderRadius: 8 }} />
          ) : (
            <div style={{ opacity: 0.75 }}>Flag data unavailable.</div>
          )}
        </>
      )}

      {hasFailed && (
        <div style={{ marginTop: 12, opacity: 0.75 }}>
          Answer: <strong>{country.answer}</strong>
        </div>
      )}
    </div>
  );
}
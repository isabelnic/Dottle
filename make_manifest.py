import json
import argparse
from pathlib import Path


def safe_int(x):
    try:
        return int(x)
    except Exception:
        return None


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def sanitize_filename(country_name: str) -> str:
    safe_name = "".join(
        ch if ch.isalnum() or ch in (" ", "_") else "_"
        for ch in (country_name or "")
    ).strip().replace(" ", "_")
    return safe_name


def build_manifest(rows, top_n: int):
    countries = {}

    for row in rows:
        iso2 = row.get("country_code")
        if not iso2:
            continue

        coords = row.get("coordinates") or {}
        lon = safe_float(coords.get("lon"))
        lat = safe_float(coords.get("lat"))
        pop = safe_int(row.get("population"))

        if lon is None or lat is None:
            continue
        if pop is None:
            continue

        name = row.get("name") or row.get("ascii_name") or str(row.get("geoname_id") or "unknown")
        country_name = row.get("cou_name_en") or iso2
        dem = safe_int(row.get("dem"))  # can be -9999 in your data

        countries.setdefault(iso2, {"answer": country_name, "cities": []})
        countries[iso2]["cities"].append(
            {"name": name, "population": pop, "dem": dem, "lat": lat, "lon": lon}
        )

    manifest = []
    for iso2, block in countries.items():
        cities = block["cities"]
        cities.sort(key=lambda c: c["population"], reverse=True)

        # If you want to exclude pop<=0 here, do it:
        cities = [c for c in cities if c["population"] and c["population"] > 0]

        chosen = cities[:top_n] if len(cities) > top_n else cities
        if not chosen:
            continue

        answer = block["answer"]
        safe_name = sanitize_filename(answer)
        file_name = f"{safe_name}.svg"

        manifest.append(
            {
                "id": iso2,
                "answer": answer,
                "file": file_name,
                "topCities": chosen,
            }
        )

    # stable order
    manifest.sort(key=lambda m: m["answer"].lower())
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cities", "-c", required=True, help="Path to cities.json")
    parser.add_argument("--svgs", "-s", required=True, help="Path to SVG folder (where country SVGs are)")
    parser.add_argument("--out", "-o", required=True, help="Output manifest.json path")
    parser.add_argument("--top-n", type=int, default=10, help="Top N cities per country")
    parser.add_argument("--only-with-svg", action="store_true", help="Only include countries that have an SVG file")
    args = parser.parse_args()

    rows = json.loads(Path(args.cities).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Expected cities.json top level to be a list")

    manifest = build_manifest(rows, top_n=args.top_n)

    if args.only_with_svg:
        svg_dir = Path(args.svgs)
        existing = {p.name for p in svg_dir.glob("*.svg")}
        manifest = [m for m in manifest if m["file"] in existing]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(manifest)} entries to {out_path}")


if __name__ == "__main__":
    main()
'''
        --countries-file path to a GeoJSON/Shapefile of country polygons
	•	--countries-iso2-field (defaults to common ISO_A2)
	•	--use-polygons to turn Mode B on
	•	--bg (transparent or white)
	•	--frame to draw a border rectangle stroke (useful if bg is transparent)

 ##Run without polygons (your current behaviour)
 python main.py -d cities.json -o images --bg white

 ##Run with Mode B polygons (mainland-only)
  python main.py -d cities.json -o images \
  --use-polygons \
  --countries-file country-shape/ne_110m_admin_0_countries.shp \
  --countries-iso2-field ISO_A2 \
  --bg transparent --frame

    Notes:
  --bg transparent keeps the SVG clean for React.
  --frame draws a subtle border so players still see the “board” boundary.
  where the geojson file comes from: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
  “Admin 0 – Countries” (110m resolution)"

'''


import json
import argparse
import math
from pathlib import Path

# New imports for polygons
try:
    import geopandas as gpd
except ImportError:
    gpd = None


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def safe_int(x):
    try:
        return int(x)
    except Exception:
        return None


def lonlat_to_xy(lon, lat, bbox, size):
    min_lon, max_lon, min_lat, max_lat = bbox
    x = (lon - min_lon) / (max_lon - min_lon) * size
    y = (max_lat - lat) / (max_lat - min_lat) * size
    return x, y


def compute_bbox(lons, lats, padding_frac):
    min_lon = min(lons)
    max_lon = max(lons)
    min_lat = min(lats)
    max_lat = max(lats)

    lon_span = max(max_lon - min_lon, 1e-9)
    lat_span = max(max_lat - min_lat, 1e-9)

    pad_lon = lon_span * padding_frac
    pad_lat = lat_span * padding_frac

    return (min_lon - pad_lon, max_lon + pad_lon, min_lat - pad_lat, max_lat + pad_lat)


def normalize_pops(pops, use_log=False, log_eps=1.0):
    if not pops:
        return []
    if use_log:
        vals = [math.log(p + log_eps) for p in pops]
    else:
        vals = pops[:]
    m = max(vals)
    if m <= 0:
        return [0.0 for _ in vals]
    return [v / m for v in vals]


def radius_from_norm(norm, r_min, r_max):
    norm = clamp(norm, 0.0, 1.0)
    return r_min + (r_max - r_min) * math.sqrt(norm)


def svg_header(size, bg="transparent", frame=False, frame_color="#DDDDDD", frame_width=2):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" viewBox="0 0 {size} {size}">\n'
    ]

    if bg == "white":
        parts.append('  <rect width="100%" height="100%" fill="white"/>\n')

    if frame:
        # Draw a border rectangle to show the "boarder" even if bg is transparent
        inset = frame_width / 2
        parts.append(
            f'  <rect x="{inset}" y="{inset}" width="{size-frame_width}" height="{size-frame_width}" '
            f'fill="none" stroke="{frame_color}" stroke-width="{frame_width}"/>\n'
        )

    return "".join(parts)


def svg_circle(x, y, r, fill="#111111"):
    return f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}"/>\n'


def svg_footer():
    return "</svg>\n"


def group_top_cities(rows, top_n, require_positive_population=True):
    countries = {}
    for row in rows:
        cc = row.get("country_code")
        if not cc:
            continue

        coords = row.get("coordinates") or {}
        lon = safe_float(coords.get("lon"))
        lat = safe_float(coords.get("lat"))
        pop = safe_int(row.get("population"))

        if lon is None or lat is None:
            continue
        if pop is None:
            continue
        if require_positive_population and pop <= 0:
            continue

        name = row.get("name") or row.get("ascii_name") or row.get("geoname_id") or "unknown"
        country_name = row.get("cou_name_en") or cc

        countries.setdefault(cc, {"country_name": country_name, "cities": []})
        countries[cc]["cities"].append(
            {"name": name, "lon": lon, "lat": lat, "population": pop}
        )

    top = {}
    insufficient = {}
    for cc, block in countries.items():
        cities = block["cities"]
        cities.sort(key=lambda d: d["population"], reverse=True)
        chosen = cities[:top_n] if len(cities) > top_n else cities
        top[cc] = {"country_name": block["country_name"], "cities": chosen}
        if len(chosen) < top_n:
            insufficient[cc] = len(chosen)

    return top, insufficient


# -----------------------------
# New: polygon bbox Mode B
# -----------------------------
# def load_mainland_bboxes(countries_file: Path, iso2_field: str):
#     """
#     Returns dict: { "FI": (min_lon, max_lon, min_lat, max_lat), ... }
#     Mode B: for MultiPolygon, keep largest polygon by area (approx).
#     """
#     if gpd is None:
#         raise ImportError(
#             "geopandas is not installed. Install with: pip install geopandas shapely pyproj"
#         )

#     gdf = gpd.read_file(countries_file)

#     if iso2_field not in gdf.columns:
#         raise ValueError(
#             f"iso2 field '{iso2_field}' not found in countries file. "
#             f"Available columns include: {list(gdf.columns)[:30]}"
#         )

#     # Ensure in WGS84 lon/lat for bounds extraction
#     if gdf.crs is None:
#         # Many files include a CRS; if yours doesn't, assume WGS84
#         gdf = gdf.set_crs("EPSG:4326")
#     else:
#         gdf = gdf.to_crs("EPSG:4326")

#     # For choosing largest polygon by area, compute area in an equal-area CRS
#     # EPSG:6933 is a common global equal-area projection.
#     gdf_area = gdf.to_crs("EPSG:6933")

#     bboxes = {}

#     for idx, row in gdf.iterrows():
#         iso2 = row[iso2_field]
#         if not iso2 or iso2 == "-99":
#             continue

#         geom = row.geometry
#         geom_area = gdf_area.loc[idx].geometry

#         if geom is None:
#             continue

#         # If MultiPolygon, select largest polygon by area (Mode B)
#         if geom.geom_type == "MultiPolygon":
#             polys = list(geom.geoms)
#             polys_area = list(geom_area.geoms)  # same ordering in projected CRS
#             if not polys:
#                 continue
#             areas = [p.area for p in polys_area]
#             k = max(range(len(areas)), key=lambda i: areas[i])
#             geom_mainland = polys[k]
#         elif geom.geom_type == "Polygon":
#             geom_mainland = geom
#         else:
#             # Unexpected geometry type (e.g. GeometryCollection)
#             try:
#                 geom_mainland = geom.convex_hull
#             except Exception:
#                 continue

#         minx, miny, maxx, maxy = geom_mainland.bounds  # lon/lat bounds
#         bboxes[str(iso2)] = (minx, maxx, miny, maxy)

#     return bboxes

def load_mainland_bboxes(countries_file: Path, iso2_field: str):
    """
    Returns:
      bboxes: { "FI": (min_lon, max_lon, min_lat, max_lat), ... }
      geoms:  { "FI": shapely Polygon (mainland only), ... }
    Mode B: for MultiPolygon, keep largest polygon by area.
    """
    if gpd is None:
        raise ImportError(
            "geopandas is not installed. Install with: pip install geopandas shapely pyproj"
        )

    gdf = gpd.read_file(countries_file)

    if iso2_field not in gdf.columns:
        raise ValueError(
            f"iso2 field '{iso2_field}' not found in countries file. "
            f"Available columns include: {list(gdf.columns)[:30]}"
        )

    # Ensure in WGS84 lon/lat for bounds extraction
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    # For choosing largest polygon by area, compute area in equal-area CRS
    gdf_area = gdf.to_crs("EPSG:6933")

    bboxes = {}
    geoms = {}

    for idx, row in gdf.iterrows():
        iso2 = row[iso2_field]
        if not iso2 or iso2 == "-99":
            continue

        geom = row.geometry
        geom_area = gdf_area.loc[idx].geometry

        if geom is None:
            continue

        if geom.geom_type == "MultiPolygon":
            polys = list(geom.geoms)
            polys_area = list(geom_area.geoms)
            if not polys:
                continue
            areas = [p.area for p in polys_area]
            k = max(range(len(areas)), key=lambda i: areas[i])
            geom_mainland = polys[k]
        elif geom.geom_type == "Polygon":
            geom_mainland = geom
        else:
            try:
                geom_mainland = geom.convex_hull
            except Exception:
                continue

        minx, miny, maxx, maxy = geom_mainland.bounds
        iso2 = str(iso2)

        bboxes[iso2] = (minx, maxx, miny, maxy)
        geoms[iso2] = geom_mainland

    return bboxes, geoms


def _ring_to_path_lonlat(coords):
    if not coords:
        return ""
    parts = [f"M {coords[0][0]} {coords[0][1]}"]
    for x, y in coords[1:]:
        parts.append(f"L {x} {y}")
    parts.append("Z")
    return " ".join(parts)


def polygon_to_lonlat_paths(poly):
    # Exterior only. (Holes can be added later if you want.)
    return [_ring_to_path_lonlat(list(poly.exterior.coords))]


def lonlat_path_to_pixel_path(path_lonlat, bbox, size):
    toks = path_lonlat.split()
    out = []
    i = 0
    while i < len(toks):
        cmd = toks[i]
        if cmd in ("M", "L"):
            lon = float(toks[i + 1])
            lat = float(toks[i + 2])
            x, y = lonlat_to_xy(lon, lat, bbox, size)
            out.extend([cmd, f"{x:.2f}", f"{y:.2f}"])
            i += 3
        else:
            # e.g. Z
            out.append(cmd)
            i += 1
    return " ".join(out)




def make_country_svg(country_code, cities, out_path, size, padding_frac, r_min, r_max, use_log,
                     bbox_override=None, outline_geom=None, outline_opacity=0.0,
                     bg="transparent", frame=False):
    lons = [c["lon"] for c in cities]
    lats = [c["lat"] for c in cities]
    pops = [float(c["population"]) for c in cities]

    if bbox_override is None:
        bbox = compute_bbox(lons, lats, padding_frac)
    else:
        # bbox_override is (min_lon, max_lon, min_lat, max_lat) then apply padding
        min_lon, max_lon, min_lat, max_lat = bbox_override
        lon_span = max(max_lon - min_lon, 1e-9)
        lat_span = max(max_lat - min_lat, 1e-9)
        pad_lon = lon_span * padding_frac
        pad_lat = lat_span * padding_frac
        bbox = (min_lon - pad_lon, max_lon + pad_lon, min_lat - pad_lat, max_lat + pad_lat)

    norms = normalize_pops(pops, use_log=use_log)
    pieces = [svg_header(size, bg=bg, frame=frame)]

    # ----- OUTLINE LAYER (hidden by default) -----
    if outline_geom is not None:
        lonlat_paths = polygon_to_lonlat_paths(outline_geom)
        px_paths = [lonlat_path_to_pixel_path(p, bbox, size) for p in lonlat_paths]

        pieces.append(f'  <g id="outline" opacity="{outline_opacity}">\n')
        for d in px_paths:
            pieces.append(f'    <path d="{d}" fill="none" stroke="#777777" stroke-width="2"/>\n')
        pieces.append("  </g>\n")

    # ----- DOTS LAYER -----
    pieces.append('  <g id="dots">\n')

    order = sorted(range(len(cities)), key=lambda i: norms[i])
    for i in order:
        c = cities[i]
        x, y = lonlat_to_xy(c["lon"], c["lat"], bbox, size)
        r = radius_from_norm(norms[i], r_min, r_max)

        x = clamp(x, r, size - r)
        y = clamp(y, r, size - r)

        pieces.append("    " + svg_circle(x, y, r))

    pieces.append("  </g>\n")
    pieces.append(svg_footer())
    out_path.write_text("".join(pieces), encoding="utf-8")

    # pieces = [svg_header(size, bg=bg, frame=frame)]

    # # draw small first, big last so big sits on top
    # order = sorted(range(len(cities)), key=lambda i: norms[i])
    # for i in order:
    #     c = cities[i]
    #     x, y = lonlat_to_xy(c["lon"], c["lat"], bbox, size)
    #     r = radius_from_norm(norms[i], r_min, r_max)

    #     # keep fully on canvas
    #     x = clamp(x, r, size - r)
    #     y = clamp(y, r, size - r)

    #     pieces.append(svg_circle(x, y, r))

    # pieces.append(svg_footer())
    # out_path.write_text("".join(pieces), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file", "-d", required=True, help="Path to JSON file")
    parser.add_argument("--out-dir", "-o", default="images", help="Output directory for SVGs")
    parser.add_argument("--top-n", type=int, default=10, help="Top N cities per country")
    parser.add_argument("--size", type=int, default=512, help="SVG width and height in pixels")
    parser.add_argument("--padding-frac", type=float, default=0.10, help="Padding around extent")
    parser.add_argument("--r-min", type=float, default=2.0, help="Minimum dot radius in px")
    parser.add_argument("--r-max", type=float, default=26.0, help="Maximum dot radius in px")
    parser.add_argument("--use-log", action="store_true", help="Log-scale population before normalising")
    parser.add_argument("--allow-zero-pop", action="store_true", help="Keep cities with population <= 0")

    # New polygon options
    parser.add_argument("--use-polygons", action="store_true",
                        help="Use country polygons for extents (Mode B: mainland only)")
    parser.add_argument("--countries-file", type=str, default=None,
                        help="Path to countries GeoJSON/Shapefile (Natural Earth admin-0 works well)")
    parser.add_argument("--countries-iso2-field", type=str, default="ISO_A2",
                        help="Column name in polygons file that stores ISO2 codes (e.g. ISO_A2)")

    # New background/frame options
    parser.add_argument("--bg", choices=["transparent", "white"], default="transparent",
                        help="SVG background fill")
    parser.add_argument("--frame", action="store_true",
                        help="Draw a border rectangle stroke as a visible frame")

    args = parser.parse_args()

    data_path = Path(args.data_file)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Expected JSON top level to be a list of city records")

    top, insufficient = group_top_cities(
        rows,
        top_n=args.top_n,
        require_positive_population=not args.allow_zero_pop,
    )

    if insufficient:
        print("Countries with fewer than top-n cities after filtering:")
        for cc, n in sorted(insufficient.items(), key=lambda x: x[0]):
            print(f"{cc}: {n}")

    # mainland_bboxes = None
    # if args.use_polygons:
    #     if args.countries_file is None:
    #         raise ValueError("--use-polygons requires --countries-file")
    #     mainland_bboxes = load_mainland_bboxes(Path(args.countries_file), args.countries_iso2_field)
    mainland_bboxes = None
    mainland_geoms = None
    if args.use_polygons:
        if args.countries_file is None:
            raise ValueError("--use-polygons requires --countries-file")
        mainland_bboxes, mainland_geoms = load_mainland_bboxes(Path(args.countries_file), args.countries_iso2_field)

    missing_poly = []

    for cc, block in top.items():
        cities = block["cities"]
        if not cities:
            continue

        country_name = block["country_name"] or cc

        # sanitize filename (spaces → underscores, remove weird chars)
        safe_name = "".join(
            ch if ch.isalnum() or ch in (" ", "_") else "_"
            for ch in country_name
        ).strip().replace(" ", "_")

        bbox_override = None
        if mainland_bboxes is not None:
            bbox_override = mainland_bboxes.get(cc)
            if bbox_override is None:
                missing_poly.append(cc)

        outline_geom = None
        if mainland_geoms is not None:
            outline_geom = mainland_geoms.get(cc)

        out_path = out_dir / f"{safe_name}.svg"

        make_country_svg(
            country_code=cc,
            cities=cities,
            out_path=out_path,
            size=args.size,
            padding_frac=args.padding_frac,
            r_min=args.r_min,
            r_max=args.r_max,
            use_log=args.use_log,
            bbox_override=bbox_override,
            outline_geom=outline_geom,     # <-- pass it here
            outline_opacity=0.0,           # hidden by default
            bg=args.bg,
            frame=args.frame,
        )

    if missing_poly:
        missing_poly = sorted(set(missing_poly))
        print(f"Warning: No polygon found for {len(missing_poly)} ISO2 codes. "
              f"These used city-bbox instead. Examples: {missing_poly[:15]}")

    print(f"Wrote SVGs to {out_dir.resolve()}")


if __name__ == "__main__":
    main()
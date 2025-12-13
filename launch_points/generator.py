"""launch_points.generator

Refactored map generation utilities originally implemented in `update_map.ipynb`.
Provides functions to load and validate marker CSVs, calculate LineString length and
generate the folium map from data files in `berlin/`.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Iterable, List, Tuple

import folium
from folium import plugins
import pandas as pd
import geopy.distance

LOGGER = logging.getLogger(__name__)


def load_markers(file_path: str, marker_type: str | None = None) -> pd.DataFrame:
    """Read a CSV file and normalize columns for marker loading.

    Normalizes header whitespace, coerces `lat`/`lon` to numeric types and
    ensures `marker_type` column exists.
    """
    df = pd.read_csv(file_path)
    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Coerce lat/lon to numeric
    for col in ("lat", "lon"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalize transport column to boolean/None
    if "transport" in df.columns:
        df["transport"] = df["transport"].apply(lambda v: _normalize_transport(v))

    if marker_type:
        df["marker_type"] = marker_type

    return df


def _normalize_transport(val):
    if pd.isna(val):
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("true", "1", "yes", "y"):  # common truthy formats
        return True
    if s in ("false", "0", "no", "n"):
        return False
    return None


def calculate_length(coords: Iterable[Tuple[float, float]]) -> float:
    """Calculate length (in kilometers) of a LineString given geojson-like coords.

    The coords are expected in [lon, lat] order (as in GeoJSON). The function
    converts to (lat, lon) tuples for geopy.
    """
    total_length = 0.0
    coords = list(coords)
    if len(coords) < 2:
        return 0.0
    for i in range(len(coords) - 1):
        # GeoJSON: [lon, lat]
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i + 1]
        total_length += geopy.distance.distance((lat1, lon1), (lat2, lon2)).km
    return total_length


def generate_map(
    markers_files: Iterable[Tuple[str, str]],
    geojson_path: str,
    station_paths: str = "berlin/station_paths.geojson",
    output_index: str = "berlin/index.html",
    output_editor: str = "berlin/editor.html",
    center: Tuple[float, float] = (52.5200, 13.4050),
    zoom_start: int = 11,
    transport_config: str = "berlin/transport_types.json",
):
    """Generate a folium map from marker CSVs and GeoJSON routes.

    markers_files: iterable of (file_path, marker_type)
    """
    # Load markers
    dfs = []
    for path, mtype in markers_files:
        if not os.path.exists(path):
            LOGGER.warning("Marker file not found: %s", path)
            continue
        dfs.append(load_markers(path, mtype))

    if dfs:
        all_markers = pd.concat(dfs, ignore_index=True)
    else:
        all_markers = pd.DataFrame()

    my_map = folium.Map(location=list(center), zoom_start=zoom_start, tiles="OpenStreetMap")

    # Load transport type config
    transport_types = {}
    if os.path.exists(transport_config):
        try:
            with open(transport_config, "r", encoding="utf-8") as f:
                transport_types = json.load(f)
        except Exception:
            LOGGER.warning("Failed to load transport types config %s", transport_config)

    # Feature groups
    layers = {
        "launch_with_transport": folium.FeatureGroup(name="Launch Points with Public Transport", show=True),
        "launch_without_transport": folium.FeatureGroup(name="Launch Points without Public Transport", show=True),
        "resting_point": folium.FeatureGroup(name="Resting Points", show=True),
    }

    def get_color(accessibility):
        if accessibility == "good":
            return "darkgreen"
        if accessibility == "moderate":
            return "orange"
        if accessibility == "poor":
            return "red"
        return "blue"

    # Add markers
    for _, row in all_markers.iterrows():
        tooltip = row.get("name")
        popup_content = f"<strong>{row.get('name')}</strong><br>"
        if pd.notna(row.get("transport")):
            popup_content += f"Public transport nearby: {'Yes' if row.get('transport') else 'No'}<br>"
        if pd.notna(row.get("picture")):
            pic = str(row.get("picture")).strip()
            popup_content += f"<img src='{pic}' width='150px'>"
        popup = folium.Popup(popup_content, max_width=300)

        icon_type = None
        if row.get("marker_type") == "resting_point":
            icon_type = folium.Icon(icon="umbrella-beach", prefix="fa", color=get_color(row.get("accessibility")))
        else:
            icon_type = folium.Icon(icon="water", prefix="fa", color=get_color(row.get("accessibility")))

        marker = folium.Marker(location=[row.get("lat"), row.get("lon")], popup=popup, tooltip=tooltip, icon=icon_type)

        mtype = row.get("marker_type")
        if mtype in layers:
            marker.add_to(layers[mtype])
        else:
            marker.add_to(my_map)

    for l in layers.values():
        l.add_to(my_map)

    # Add GeoJSON routes
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        line_layer = folium.FeatureGroup(name="Paddel Routes", show=True)

        def style_function(feature):
            style_dict = {}
            if feature.get("properties", {}).get("sidetrack") is True:
                style_dict["dashArray"] = "5, 10"
            return style_dict

        def highlight_function(feature):
            return {"weight": 6, "opacity": 1.0}

        for feature in geojson_data.get("features", []):
            coords = feature["geometry"]["coordinates"]
            line_length = calculate_length(coords)
            waterbody = feature.get("properties", {}).get("waterbody", "")
            geojson = folium.GeoJson(
                data=feature,
                tooltip=f"{waterbody} | {line_length:.1f} km",
                popup=folium.Popup(
                    f"<strong>Start:</strong> {feature.get('properties', {}).get('start','')}<br><strong>End:</strong> {feature.get('properties', {}).get('end','')}<br><strong>Length:</strong> {line_length:.2f} km",
                    max_width=300,
                ),
                style_function=style_function,
                highlight_function=highlight_function,
            )
            geojson.add_to(line_layer)

        line_layer.add_to(my_map)
    else:
        LOGGER.warning("GeoJSON file not found: %s", geojson_path)

    # Add station paths and station markers (optional)
    if os.path.exists(station_paths):
        with open(station_paths, "r", encoding="utf-8") as f:
            station_data = json.load(f)

        station_layer = folium.FeatureGroup(name="Station Paths", show=True)

        def station_style(feature):
            # dark grey dotted line
            return {"color": "#4a4a4a", "dashArray": "1, 6", "weight": 3, "opacity": 0.9, "lineCap": "round"}

        for feature in station_data.get("features", []):
            geom = feature.get("geometry", {})
            if geom.get("type") != "LineString":
                continue
            coords = geom.get("coordinates", [])
            if not coords:
                continue

            # Path will be added below with tooltip showing its length

            # The first vertex denotes the public transport station
            first = coords[0]
            try:
                lon, lat = first
            except Exception:
                continue

            props = feature.get("properties", {})
            # Accept either 'station_name' or 'name'
            station_name = props.get("station_name") or props.get("name") or "Station"
            station_type = (props.get("station_type") or props.get("type") or "bus").lower()

            # compute path length and add as tooltip to the path
            line_length = calculate_length(coords)
            # choose icon class (Font Awesome 6 style) and color
            # Choose icon class from config if available
            icon_class = "fa-solid fa-bus"
            if station_type in transport_types and isinstance(transport_types[station_type], dict):
                icon_class = transport_types[station_type].get("icon", icon_class)
            color = "#4a4a4a"

            station_popup = folium.Popup(f"<strong>{station_name}</strong><br>Type: {station_type}", max_width=300)
            # Use a DivIcon to allow custom FA class and consistent color
            # Make the station icon large (approx. 2/3 the size of typical launch point icons)
            icon_html = f"<i class='{icon_class}' style='color: {color}; font-size: 20px;'></i>"
            station_icon = folium.DivIcon(html=icon_html)
            # Include distance in the station tooltip as meters (not km)
            meters = line_length * 1000.0
            # Round to nearest 25 meters for walking distances
            rounded_meters = int(round(meters / 25.0) * 25)
            station_tooltip = folium.Tooltip(f"{station_name} — {rounded_meters:.0f} m")
            folium.Marker(location=[lat, lon], popup=station_popup, tooltip=station_tooltip, icon=station_icon).add_to(station_layer)
            # Add a GeoJson for this feature with a tooltip showing its length
            folium.GeoJson(data=feature, style_function=station_style, tooltip=folium.Tooltip(f"{rounded_meters:.0f} m")).add_to(station_layer)
        station_layer.add_to(my_map)

    # Add controls
    # Import plugins directly to avoid relying on folium attaching a `plugins`
    # attribute to the top-level package object in some environments.
    plugins.LocateControl(auto_start=False).add_to(my_map)
    folium.LayerControl().add_to(my_map)
    plugins.Draw(export=True).add_to(my_map)

    os.makedirs(os.path.dirname(output_index), exist_ok=True)
    my_map.save(output_index)
    my_map.save(output_editor)


def validate_geojson(path: str) -> bool:
    """Basic validation of the GeoJSON file structure."""
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("type") != "FeatureCollection":
        return False
    for feat in data.get("features", []):
        if feat.get("geometry", {}).get("type") != "LineString":
            return False
    return True


def load_transport_types(path: str = "berlin/transport_types.json") -> dict:
    """Load a transport types JSON mapping.

    Returns a dict mapping station_type key to an object with keys 'name' and 'icon'.
    If the file isn't present or fails to load, returns an empty dict.
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        LOGGER.warning("Failed to load transport types from %s", path)
    return {}


def validate_station_paths(path: str, transport_config: str = "berlin/transport_types.json") -> bool:
    """Validate optional station paths GeoJSON.

    Returns True if the file is absent (file is optional) or if present and structurally valid.
    Each feature must be a LineString; properties should include a station name and a station type
    (accepted types: train, tram, bus) — keys accepted: 'station_name' or 'name', and
    'station_type' or 'type'.
    """
    if not os.path.exists(path):
        # Station paths are optional
        return True
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False

    if data.get("type") != "FeatureCollection":
        return False

    # Load transport types for validation (optional)
    allowed_types = set(("train", "tram", "bus"))
    if os.path.exists(transport_config):
        try:
            with open(transport_config, "r", encoding="utf-8") as f:
                transport_types = json.load(f)
                if isinstance(transport_types, dict):
                    allowed_types = set(transport_types.keys())
        except Exception:
            pass

    for feat in data.get("features", []):
        geom = feat.get("geometry", {})
        if geom.get("type") != "LineString":
            return False
        coords = geom.get("coordinates", [])
        if not coords or len(coords) < 2:
            return False
        props = feat.get("properties", {})
        name = props.get("station_name") or props.get("name")
        stype = (props.get("station_type") or props.get("type") or "").lower()
        if not name or stype not in allowed_types:
            return False

    return True


if __name__ == "__main__":
    # Simple CLI entrypoint for quick manual runs
    import argparse

    parser = argparse.ArgumentParser(description="Generate folium map from project data")
    parser.add_argument("--output-index", default="berlin/index.html")
    parser.add_argument("--output-editor", default="berlin/editor.html")
    parser.add_argument("--geojson", default="berlin/routes.geojson")
    args = parser.parse_args()

    markers = [
        ("berlin/launch_with_transport.csv", "launch_with_transport"),
        ("berlin/launch_without_transport.csv", "launch_without_transport"),
        ("berlin/resting_points.csv", "resting_point"),
    ]
    generate_map(markers, args.geojson, args.output_index, args.output_editor)

#!/usr/bin/env python
"""Small CLI wrapper to run the map generator."""
from launch_points.generator import generate_map

if __name__ == "__main__":
    markers = [
        ("berlin/launch_with_transport.csv", "launch_with_transport"),
        ("berlin/launch_without_transport.csv", "launch_without_transport"),
        ("berlin/resting_points.csv", "resting_point"),
    ]
    generate_map(markers, "berlin/routes.geojson")

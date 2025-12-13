# Launchpoints Berlin 🛶

Launch Points for folding kayaks, SUPs and other collapsible water craft that can be transported on public transit. This repository contains data and tools to create an interactive Folium map of:

- Launch points (with or without nearby public transport)
- Walkways to nearest public transport
- Resting points
- Paddling routes (LineString features with distance)

The map generation is implemented in `launch_points/generator.py` and can be run via the CLI (`python -m launch_points.cli generate`) to produce the static outputs `berlin/index.html` (public map) and `berlin/editor.html` (interactive editor view with drawing tools).

Yes, currently only a single map (Berlin) is implemented - I started the project because I wanted the map :)

---

## Quick usage — edit data and rebuild the map ✅

1. Open the interactive editor:

	 - Open `berlin/editor.html` in your browser. This map includes drawing tools (via Leaflet.Draw) so you can add or edit markers and routes temporarily.

2. Create or edit features:

	 - Use the draw toolbar to add a marker (point) or a line (route).
	 - After drawing, you can either:
		 - Click the feature to see its information (popups/tooltips may show coordinates which you can copy to clipboard), or
		 - Use the Draw plugin's **Export** button to obtain a GeoJSON representation of your edits and copy it to the clipboard.

3. Add features to the source data files:

	 - Markers (launch points / resting points) are stored as CSV files in `berlin/`:

		 - `berlin/launch_with_transport.csv`
		 - `berlin/launch_without_transport.csv`
		 - `berlin/resting_points.csv`

		 CSV expected columns (example):

		 ```csv
		 name,lat,lon,transport,accessibility,picture
		 Licht und Luftbad Müggelsee,52.446309,13.67013,True,good,figs/launch_lichluftbad.jpg
		 ```

		 Notes:
		 - Header names should be trimmed (no leading/trailing spaces). The validator script strips and checks header whitespace for you.
		 - `transport` can be `True`/`False` or empty (nullable). `accessibility` is free-text but typically `good`, `moderate`, `poor`.
		 - `picture` should be a path relative to the CSV file (e.g., `figs/xxx.jpg`). Validate that the referenced files exist before committing.

			Adding pictures and images
			--------------------------
			Contributors can add pictures for markers to improve the popups on the map. Follow these recommendations for best results:

			- Storage location: put images inside `berlin/figs/` (preferred). Historically the project also references `fig/` — prefer `figs/` for new content.
			- File path: set the `picture` CSV column to a path relative to the CSV file, e.g. `figs/launch_lichluftbad.jpg`.
			- File names: use lowercase, hyphenated filenames (no spaces), e.g. `launch_lichluftbad.jpg`.
			- File formats: JPEG (`.jpg`/`.jpeg`) and PNG (`.png`) are widely supported. Avoid remote URLs unless you intentionally host images externally (the validator only checks local files).
			- Image size: keep files reasonably small to improve load times (suggested max ~400 KB); the popup image width is constrained to 150px in the default generator (we recommend scaling and compressing source images to ~600px width while keeping file sizes small).
			- CSV example row:

				```csv
				name,lat,lon,transport,accessibility,picture
				Licht und Luftbad Müggelsee,52.446309,13.67013,True,good,figs/launch_lichluftbad.jpg
				```

			- Validator behavior: the validator checks for picture existence relative to the CSV file and will report `missing-picture: row N -> <path>` if the file is not found. To avoid validation errors, place the picture in `berlin/figs/` and use the relative path in `picture`.
			- Customizing popup size: the generator sets the popup image width to 150px (`<img width='150px'>`). If you want a different display size, edit `launch_points/generator.py` where the popup HTML is constructed.
			- Publishing: when publishing generated HTML (e.g., to GitHub Pages), ensure images from `berlin/figs/` are included in the published paths so they load correctly on the site.


	 - Routes are stored in GeoJSON (`berlin/routes.geojson`). Each feature should be a `LineString` and may include properties such as:

		 ```json
		 {
			 "type": "Feature",
			 "properties": {"start": "A", "end": "B", "waterbody": "Spree", "sidetrack": true},
			 "geometry": {"type": "LineString", "coordinates": [[lon, lat], [lon, lat], ...]}
		 }
		 ```

		 Important: GeoJSON coordinates are in [lon, lat] order. The map generator converts these to (lat, lon) for distance calculations.

	### Station paths (optional)

	If you want to include walking paths from launch points to nearby public transport stations, add a `berlin/station_paths.geojson` file with `LineString` features. The generator expects the **first vertex** of each LineString to denote the station location. Each feature should include properties:


	Behavior:


	Example feature:

	```json
	{
		"type": "Feature",
		"properties": {"station_name": "Central Station", "station_type": "train"},
		"geometry": {"type": "LineString", "coordinates": [[lon, lat], [lon, lat], ...]}
	}
	```


	### Transport types configuration

	Transport icons are configurable via `berlin/transport_types.json`. This file maps transport type keys (used in `station_type`) to a small object that includes `name` and `icon` (Font Awesome class). The generator loads this file to choose the icon to render for station markers.

	Example `berlin/transport_types.json`:

	```json
	{
		"train": {"name": "Train", "icon": "fa-solid fa-train"},
		"tram": {"name": "Tram", "icon": "fa-solid fa-train-tram"},
		"bus": {"name": "Bus", "icon": "fa-solid fa-bus"},
		"metro": {"name": "U-Bahn", "icon": "fa-solid fa-train-subway"}
	}
	```

	To add new transport types (e.g. `metro` or `cablecar`), add a new key with the relevant `name` and `icon` and then reference the key value as `station_type` in your station paths GeoJSON.

4. Validate your data locally:

	 - A validator is available at `launch_points/validator.py`. To run it from Python:

		 ```python
		 from launch_points import validator
		 issues = validator.validate_marker_csv('berlin/launch_with_transport.csv')
		 print(issues)
		 ```

	 - Or run it as a script for one or more CSV files:

		 ```powershell
		 conda run -n launch_points python -m launch_points.validator berlin/launch_with_transport.csv berlin/resting_points.csv
		 ```

5. Rebuild the map:

 	- Run the generator via the CLI (recommended):

 	```powershell
 	python -m launch_points.cli generate
 	```

 	- Tests and automated validation (recommended):

		 ```powershell
		 conda activate launch_points
		 conda run -n launch_points python -m unittest discover -s tests -v
		 ```

	### Command-line (optional)

	You can also run lightweight project commands from the command line using the bundled CLI module.

	Examples:

	```powershell
	# Validate CSVs and print a JSON report but do not fail with non-zero exit
	python -m launch_points.cli validate --format json --no-exit-on-error

	# Dry-run map generation (does not write files) and skip validation
	python -m launch_points.cli generate --dry-run --no-validate
	```

	Note: The CLI uses the repository defaults and does not (currently) accept file path arguments; use the notebook or edit `berlin/*.csv` and `berlin/routes.geojson` manually.

	When errors occur, the CLI now provides short, actionable guidance. Typical suggestions include:

	- For missing pictures: put the image files in `berlin/figs/` (or correct the `picture` paths in the CSV).
	- For non-numeric coordinates: ensure `lat`/`lon` contain decimal numbers (e.g., `52.446309`).
	- For unknown `transport` values: use `True`/`False` or leave blank.
	- For header whitespace: run `python -m launch_points.cli validate --fix` to auto-fix header whitespace.

	If an unexpected exception occurs during generation, the CLI will print a brief explanation of likely causes and recommended next steps (e.g., run the validator, inspect the notebook interactively), followed by the full traceback for debugging.

6. Publish the map:

	 - Commit changes to the CSV/GeoJSON files and the generated `berlin/index.html` (or publish via a CI job to `gh-pages`). Note: You prefer to handle commits yourself — I will remind you when there are safe points to commit (after validation/tests).


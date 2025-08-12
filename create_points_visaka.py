# Treepedia createPoints.py – Updated
# Generates points along streets every mini_dist meters with attributes
# Last updated: July 2025 by OpenAI for extended metadata traceability

def createPoints(inshp, outshp, mini_dist):
    import fiona
    import os
    from shapely.geometry import shape, mapping
    from shapely.ops import transform
    from functools import partial
    import pyproj
    from fiona.crs import from_epsg

    # Exclude major roads, highways, footpaths
    excluded_highways = {
        'trunk_link', 'tertiary', 'motorway', 'motorway_link', 'steps', None, ' ',
        'pedestrian', 'primary', 'primary_link', 'footway', 'tertiary_link',
        'trunk', 'secondary', 'secondary_link', 'bridleway', 'service'
    }

    # Prepare cleaned temp shapefile path
    root = os.path.dirname(inshp)
    basename = 'clean_' + os.path.basename(inshp)
    temp_cleanedStreetmap = os.path.join(root, basename)

    if os.path.exists(temp_cleanedStreetmap):
        fiona.remove(temp_cleanedStreetmap, 'ESRI Shapefile')

    # Clean input shapefile (remove excluded highway types)
    with fiona.open(inshp) as source, fiona.open(
        temp_cleanedStreetmap, 'w',
        driver=source.driver, crs=source.crs, schema=source.schema
    ) as dest:
        for feat in source:
            try:
                highway = feat['properties']['highway']
                if highway in excluded_highways:
                    continue
            except:
                key = list(dest.schema['properties'].keys())[0]
                val = feat['properties'][key]
                if val in excluded_highways:
                    continue
            dest.write(feat)

    # Define output point schema
    schema = {
        'geometry': 'Point',
        'properties': {
            'point_id': 'int',
            'street_id': 'str',
            'street_name': 'str'
        },
    }

    total_points = 0

    # Create output point shapefile
    if not os.path.exists(os.path.dirname(outshp)):
        os.makedirs(os.path.dirname(outshp), exist_ok=True)

    with fiona.Env():
        with fiona.open(outshp, 'w', crs=from_epsg(4326), driver='ESRI Shapefile', schema=schema) as output:
            for line in fiona.open(temp_cleanedStreetmap):
                try:
                    geom = shape(line['geometry'])
                    length = geom.length

                    street_id = line['properties'].get('osm_id', 'NA')
                    street_name = line['properties'].get('name', 'NA')

                    # Project to meters
                    project = partial(
                        pyproj.transform,
                        pyproj.Proj(init='EPSG:4326'),
                        pyproj.Proj(init='EPSG:3857')
                    )
                    geom_m = transform(project, geom)
                    line_len = geom_m.length

                    # Interpolate points along line
                    if line_len < mini_dist:
                        point = geom_m.interpolate(line_len / 2)
                        back_proj = partial(
                            pyproj.transform,
                            pyproj.Proj(init='EPSG:3857'),
                            pyproj.Proj(init='EPSG:4326')
                        )
                        point = transform(back_proj, point)
                        output.write({
                            'geometry': mapping(point),
                            'properties': {
                                'point_id': total_points,
                                'street_id': str(street_id),
                                'street_name': str(street_name)
                            }
                        })
                        total_points += 1
                    else:
                        for distance in range(0, int(line_len), mini_dist):
                            point = geom_m.interpolate(distance)
                            back_proj = partial(
                                pyproj.transform,
                                pyproj.Proj(init='EPSG:3857'),
                                pyproj.Proj(init='EPSG:4326')
                            )
                            point = transform(back_proj, point)
                            output.write({
                                'geometry': mapping(point),
                                'properties': {
                                    'point_id': total_points,
                                    'street_id': str(street_id),
                                    'street_name': str(street_name)
                                }
                            })
                            total_points += 1

                except Exception as e:
                    print(f"[ERROR] Skipping segment due to error: {e}")
                    continue

    print(f"✅ Point generation complete. Total points created: {total_points}")
    fiona.remove(temp_cleanedStreetmap, 'ESRI Shapefile')


# ------------ Main ------------
if __name__ == "__main__":
    import os

    inshp = r'C:\Treepedia_Public-master\india_city_shapefiles\Visakhapatnam\visakhapatnam.shp'
    outshp = r'C:\Treepedia_Public-master\india_city_shapefiles\Visakhapatnam\create_points\create_points.shp'
    mini_dist = 20  # meters between points

    createPoints(inshp, outshp, mini_dist)

from sidekick import lazy


class GeoAttribute:
    """
    F.geo.* namespace.
    """

    @lazy
    def _gis(self):
        import django.contrib.gis.db.models.functions as functions

        return functions

    def __init__(self, f_expr):
        self.expr = f_expr
        self.name = f_expr.name

    def __repr__(self):
        return "F.%s.geo" % self.name

    # Gis properties
    area = property(lambda self: self._gis.Area)
    centroid = property(lambda self: self._gis.Centroid(self))
    envelope = property(lambda self: self._gis.Envelope(self))
    mem_size = property(lambda self: self._gis.MemSize(self))
    num_geometries = property(lambda self: self._gis.NumGeometries(self))
    num_points = property(lambda self: self._gis.NumPoints(self))
    perimeter = property(lambda self: self._gis.Perimeter(self))
    point_on_surface = property(lambda self: self._gis.PointOnSurface(self))

    # TODO: Spatial lookups
    # contained = method('contained')
    # coveredby = method('coveredby')
    # covers = method('covers')
    # crosses = method('crosses')
    # disjoint = method('disjoint')
    # equals = method('equals')
    # intersects = method('intersects')
    # relate = starmethod('relate')
    # touches = method('touches')
    # left = method('left')
    # right = method('right')
    # above = method('strictly_above')
    # below = method('strictly_below')

    # TODO: Gis functions
    # geojson = method(self._gis.AsGeoJSON)
    # gml = method(self._gis.AsGML)
    # kml = method(self._gis.AsKML)
    # svg = method(self._gis.AsSVG)
    # bounding_circle = method(self._gis.BoundingCircle)
    # difference = method(self._gis.Difference)
    # distance = method(self._gis.Distance)
    # force_rhr = method(self._gis.ForceRHR)
    # geohash = method(self._gis.GeoHash)  # __hash__ requires an int
    # intersection = method(self._gis.Intersection)
    # make_valid = method(self._gis.MakeValid)
    # reverse = method(self._gis.Reverse)
    # scale = method(self._gis.Scale)
    # snap_to_grid = method(self._gis.SnapToGrid)
    # symmetric_difference = method(self._gis.SymDifference)
    # transform = method(self._gis.Transform)
    # translate = method(self._gis.Translate)
    # union = method(self._gis.Union)

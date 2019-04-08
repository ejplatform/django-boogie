from ..django_conf import Conf


class CompressorConf(Conf):
    # Django compressor
    COMPRESS_ENABLED = True
    COMPRESS_CSS_FILTERS = [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.rCSSMinFilter",
    ]
    COMPRESS_PRECOMPILERS = [
        ("text/coffeescript", "coffee --compile --stdio"),
        ("text/less", "lessc {infile} {outfile}"),
        ("text/x-sass", "sass {infile} {outfile}"),
        ("text/x-scss", "sass --scss {infile} {outfile}"),
        ("text/stylus", "stylus < {infile} > {outfile}"),
    ]

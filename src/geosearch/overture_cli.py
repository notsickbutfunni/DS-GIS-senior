"""Run the overturemaps CLI with a User-Agent header.

stac.overturemaps.org is behind Cloudflare, which answers 403 to Python's
default "Python-urllib/x.y" User-Agent. overturemaps 1.0.2 calls urlopen()
without one, so every download fails before it starts ("Could not fetch STAC
catalog: HTTP Error 403"). A global opener with a User-Agent fixes all of its
urlopen() calls.

Usage (same arguments as the overturemaps CLI):
    uv run python -m geosearch.overture_cli download --bbox=W,S,E,N -f geoparquet --type=place -o places.parquet
"""

import urllib.request

from overturemaps.cli import cli


def main() -> None:
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "geosearch (overturemaps-py)")]
    urllib.request.install_opener(opener)
    cli(prog_name="overturemaps")


if __name__ == "__main__":
    main()

from rapidfuzz import process, utils, fuzz
import webcolors
import re

_basic_colors = {webcolors.name_to_hex(c)[1:]: c for c in webcolors.names()}
_regex = r'^#?[A-Fa-f0-9]*$'


class SearchResult:
    def __init__(self, hex, is_name):
        self.hex = hex
        self.is_name = is_name


def get_similarity(a: str, b: str) -> float:
    return fuzz.WRatio(a, b, processor=utils.default_process)


def search(
    query, *, additional_colors=None, n=5
) -> list[tuple[str, float, str]]:
    """Returns (name, similarity, hex)"""

    if additional_colors is None:
        colors = _basic_colors
    else:
        colors = _basic_colors | {v: k for k, v in additional_colors.items()}

    return process.extract(
        query,
        colors,
        scorer=fuzz.WRatio,
        processor=utils.default_process,
        limit=n,
        score_cutoff=70,
    )


def get_color(
    query: str, *, additional_colors=None
) -> list[tuple[str, str]] | None:
    """Returns (hex, name), name might be None"""
    if re.match(_regex, query):
        if query.startswith('#') and len(query) == 7:
            return [(query[1:], None)]
        if not query.startswith('#') and len(query) == 6:
            return [(query, None)]
        return None
    res = search(query, additional_colors=additional_colors)
    return [(hex, name) for name, _, hex in res]

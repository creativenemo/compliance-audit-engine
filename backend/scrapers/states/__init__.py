from .co import ColoradoScraper
from .dc import DCscraper
from .de import DelawareScraper
from .fl import FloridaScraper
from .il import IllinoisScraper
from .tn import TennesseeScraper
from .va import VirginiaScraper
from .wa import WashingtonScraper
from .wy import WyomingScraper

TIER1_SCRAPERS = {
    "DE": DelawareScraper(),
    "WY": WyomingScraper(),
    "FL": FloridaScraper(),
    "CO": ColoradoScraper(),
    "IL": IllinoisScraper(),
    "VA": VirginiaScraper(),
    "TN": TennesseeScraper(),
    "WA": WashingtonScraper(),
    "DC": DCscraper(),
}

__all__ = [
    "ColoradoScraper",
    "DCscraper",
    "DelawareScraper",
    "FloridaScraper",
    "IllinoisScraper",
    "TennesseeScraper",
    "VirginiaScraper",
    "WashingtonScraper",
    "WyomingScraper",
    "TIER1_SCRAPERS",
]

try:
    from ._version import __version__
except Exception:
    __version__ = "0+unknown"

from .api import AstarsError
from .api import Diagnostic
from .api import ParserUnavailableError
from .api import SourceSpan
from .api import SourceUnit
from .api import UnsupportedLanguageError
from .api import parse_bytes
from .api import parse_file
from .api import parse_str

__all__ = [
    "__version__",
    "AstarsError",
    "Diagnostic",
    "ParserUnavailableError",
    "SourceSpan",
    "SourceUnit",
    "UnsupportedLanguageError",
    "parse_bytes",
    "parse_file",
    "parse_str",
]

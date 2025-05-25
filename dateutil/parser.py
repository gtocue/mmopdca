from datetime import datetime


def parse(timestr, *args, **kwargs):
    """Parse a date/time string.

    This function provides a minimal implementation that mimics
    :func:`dateutil.parser.parse` for the limited use within the
    project.  The parameter name ``timestr`` matches the signature
    expected by type checkers and callers.
    """

    if timestr.endswith("Z"):
        timestr = timestr[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(timestr)
    except ValueError:
        # Fallback to naive parsing of date only
        try:
            return datetime.strptime(timestr, "%Y-%m-%d")
        except Exception:
            raise ValueError(f"Unrecognized date string: {timestr}")
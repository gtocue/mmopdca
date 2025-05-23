from datetime import datetime

def parse(date_str, *args, **kwargs):
    # Very minimal ISO8601 parser
    if date_str.endswith('Z'):
        date_str = date_str[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        # Fallback to naive parsing of date only
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            raise ValueError(f"Unrecognized date string: {date_str}")
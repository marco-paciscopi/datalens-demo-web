import html


def sanitize_value(value):
    """Sanitize a value to prevent XSS."""
    if isinstance(value, str):
        # Escape HTML characters
        return html.escape(value, quote=False)
    elif isinstance(value, (list, tuple)):
        # Recursively sanitize elements in lists or tuples
        return [sanitize_value(item) for item in value]
    elif isinstance(value, dict):
        # Recursively sanitize values in nested dictionaries
        return {key: sanitize_value(val) for key, val in value.items()}
    else:
        # For other types, return the value as is
        return value


def sanitize_dict(input_dict):
    """Sanitize a dictionary to prevent XSS."""
    return sanitize_value(input_dict)

from django import template
import re

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a key.
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    
    # If it's not a dictionary, try to access as attribute or return None
    try:
        return getattr(dictionary, key)
    except (AttributeError, TypeError):
        return None


@register.filter
def clean_markdown(text):
    """
    Clean markdown formatting and theme labels from text
    """
    if not text or text == "":
        return ""
    
    # Convert to string if needed
    text = str(text)
    
    # Remove markdown bold markers
    text = text.replace('**', '')
    
    # Extract content after theme labels
    theme_pattern = r'\[Theme:[^\]]*\]\s*(.*?)$'
    theme_match = re.search(theme_pattern, text, re.DOTALL)
    if theme_match and theme_match.group(1).strip():
        text = theme_match.group(1).strip()
    
    # Remove any remaining theme labels
    text = re.sub(r'\[Theme:[^\]]*\]', '', text)
    
    # Remove any other bracketed content
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Remove step labels if they appear at the beginning
    text = re.sub(r'^[A-J]\.\s*', '', text)
    
    # Remove any leftover special characters
    text = re.sub(r'[\[\]\(\)]', '', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Capitalize first letter if it's lowercase
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    
    return text.strip()


@register.filter
def is_fragment(text):
    """
    Check if text is a corrupted fragment that needs editing
    """
    if not text or text == "":
        return False
    
    text = str(text).strip()
    
    # If text is empty after stripping, it's a fragment
    if not text:
        return True
    
    # Check for common fragment patterns
    fragment_patterns = [
        r'^[A-Z][a-z]{0,3}$',  # Single short word like "E", "M", "Ve"
        r'^[A-Za-z]{1,5}$',     # Very short word (1-5 letters)
        r'^[A-Za-z]+ing$',      # Word ending with "ing" like "Uilding"
        r'^Eme:',                # Starts with "Eme:"
        r'^[A-Za-z]+/[A-Za-z]+$', # Contains slash like "Assessment/Synt"
        r'^[A-Za-z]{1,3}\s+[A-Za-z]{1,3}$', # Two very short words
    ]
    
    for pattern in fragment_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # Check for theme labels that weren't properly extracted
    if re.search(r'Theme:|Eme:', text, re.IGNORECASE):
        return True
    
    # If text is longer than 15 characters and contains spaces, it's probably fine
    if len(text) > 15 and ' ' in text:
        return False
    
    # Check if it looks like a truncated sentence
    common_endings = ['ing', 'ion', 'tion', 'ment', 'ly', 'al', 'ic', 'ive']
    if len(text) < 20 and any(text.lower().endswith(ending) for ending in common_endings):
        if ' ' not in text:  # Single word with common ending
            return True
    
    return False

@register.filter
def get_range(value):
    """
    Template filter to create a range of numbers.
    Usage: {% for i in 5|get_range %} ... {% endfor %}
    """
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)


@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument.
    Usage: {{ value|multiply:5 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """
    Subtract argument from value.
    Usage: {{ value|subtract:5 }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """
    Divide value by argument.
    Usage: {{ value|divide:5 }}
    """
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    """Convert markdown text to HTML"""
    if not text:
        return ''
    return mark_safe(md.markdown(text, extensions=['extra', 'nl2br']))
from django import template
register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply numerical value by arg in templates."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""

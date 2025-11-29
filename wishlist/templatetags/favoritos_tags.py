from django import template
from ..models import Favorito

register = template.Library()

@register.simple_tag
def es_favorito(usuario, producto):
    """Verifica si un producto está en favoritos del usuario"""
    if usuario.is_authenticated:
        return Favorito.objects.filter(usuario=usuario, producto=producto).exists()
    return False

@register.simple_tag
def contar_favoritos(usuario):
    """Cuenta los favoritos del usuario"""
    if usuario.is_authenticated:
        return Favorito.objects.filter(usuario=usuario).count()
    return 0
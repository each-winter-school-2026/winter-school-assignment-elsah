from django import template

register = template.Library()

@register.inclusion_tag('block/card_wrapper.html')
def generateCard(card, insertionMode=False):
    return {'card': card, 'insertionMode': insertionMode}
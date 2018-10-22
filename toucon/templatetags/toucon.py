from commonmark import commonmark as marked
from django import template
from django.template.base import Node
from django.utils.safestring import mark_safe


register = template.Library()


@register.simple_tag
def active(request, patterns):
    if patterns:
        for pattern in patterns.split(','):
            try:
                if pattern == request.resolver_match.url_name:
                    return 'active'
            except Exception as e:
                return ''
    return ''


@register.filter
def markdown(text):
    return mark_safe(marked(text))


@register.tag(name='markdown')
def do_markdown(parser, token):
    nodelist = parser.parse(('endmarkdown',))
    parser.delete_first_token()
    bits = token.split_contents()
    if len(bits) > 1:
        raise template.TemplateSyntaxError('`markdown` tag requires exactly zero arguments')
    return MarkdownNode(nodelist)


class MarkdownNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        text = self.nodelist.render(context)
        return mark_safe(marked(text))

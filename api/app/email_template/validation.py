"""Checks every variable a template uses against its email type's schema.

Rendering with strict undefined variables only catches mistakes on the branch
the sample data happens to take; this reads every path in the template -
including ones inside an `if` that is false for the sample, or a loop over an
empty list - so a misspelt `{{ offer.expiry_dat }}` is reported when the
template is saved, not when someone's email goes out without it.
"""
from liquid.context import RenderContext

from app.email_template import engine
from app.email_template.engine import EmailRenderError
from app.email_template.views import ListOf, SCALAR_TYPES, _is_view


#: Properties Liquid provides on lists and strings.
_LIST_PROPERTIES = {'size', 'first', 'last'}
_STRING_PROPERTIES = {'size'}
_LIQUID_GLOBALS = {'forloop', 'tablerowloop', 'empty', 'blank', 'nil', 'null', 'true', 'false'}

_LIST_ITEM = object()


def _node_type(spec):
    """Normalise a View class / ListOf / scalar name into ('object', View) etc."""
    if isinstance(spec, ListOf):
        return 'list', spec.item
    if _is_view(spec):
        return 'object', spec
    return 'scalar', spec


def _walk_path(root_view, segments):
    """None if `segments` (after the root name) is a valid path from the view,
    else the first segment that isn't."""
    kind, spec = 'object', root_view
    for segment in segments:
        if not isinstance(segment, (str, int)) and segment is not _LIST_ITEM:
            return None  # a computed index (a[b]) - can't be checked statically
        if kind == 'object':
            field = spec.fields.get(segment) if isinstance(segment, str) else None
            if field is None:
                return segment
            kind, spec = _node_type(field.type)
        elif kind == 'list':
            if segment is _LIST_ITEM or isinstance(segment, int) or segment in ('first', 'last'):
                kind, spec = _node_type(spec)
            elif segment == 'size':
                kind, spec = 'scalar', 'number'
            else:
                return segment
        else:
            if segment in _STRING_PROPERTIES and spec in SCALAR_TYPES:
                kind, spec = 'scalar', 'number'
            else:
                return segment
    return None


def _segments(path_expression):
    segments = getattr(path_expression, 'path', None)
    if segments is None:
        return None
    return [s if isinstance(s, (str, int)) else None for s in segments]


def _bindings(template):
    """{name: [root, segments...]} for loop variables (and assigns of a plain
    path), so `grant.name` inside `for grant in offer.grants` is checked as
    offer.grants[item].name. Names bound to anything else map to None."""
    bindings = {}
    static_context = RenderContext(template)

    def resolve(segments):
        if not segments or segments[0] is None:
            return None
        root = segments[0]
        if root in bindings:
            base = bindings[root]
            return None if base is None else base + segments[1:]
        return segments

    def visit(nodes):
        for node in nodes:
            kind = type(node).__name__
            if kind == 'ForNode':
                expression = node.expression
                iterable = resolve(_segments(expression.iterable))
                bindings[str(expression.identifier)] = (
                    None if iterable is None else iterable + [_LIST_ITEM])
            elif kind == 'AssignNode':
                left = getattr(node.expression, 'left', None)
                filters = getattr(node.expression, 'filters', None)
                path = resolve(_segments(left)) if left is not None and not filters else None
                bindings[str(node.name)] = path
            elif kind == 'CaptureNode':
                bindings[str(getattr(node, 'name', ''))] = None
            visit(node.children(static_context, include_partials=False))

    visit(template.nodes)
    return bindings


def _position(source, index):
    if index is None or index < 0:
        return None, None
    before = source[:index]
    return before.count('\n') + 1, index - (before.rfind('\n') + 1) + 1


def check_template(source, context_views, field='body'):
    """Raises EmailRenderError for a syntax error or the first path that the
    context doesn't have."""
    template = engine.parse(source, engine.HTML, strict=True, field=field)
    bindings = _bindings(template)
    analysis = template.analyze()

    for name, occurrences in analysis.variables.items():
        for variable in occurrences:
            segments = list(variable.segments)
            root = segments[0] if segments else None
            if root in _LIQUID_GLOBALS:
                continue
            if root in bindings:
                base = bindings[root]
                if base is None:
                    continue
                segments = base + segments[1:]
                root = segments[0]
            view = context_views.get(root)
            if view is None:
                line, column = _position(source, variable.span.index)
                raise EmailRenderError(
                    '"{}" is not available in this email'.format(root), line, column, field)
            bad = _walk_path(view, segments[1:])
            if bad is not None:
                line, column = _position(source, variable.span.index)
                raise EmailRenderError(
                    '"{}" has no field "{}"'.format(str(variable), bad), line, column, field)

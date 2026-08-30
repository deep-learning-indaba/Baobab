"""Derived placeholders: a value computed from an ordered rule set rather than
read from a single source - design section 5.7.

Kept separate from resolver.py because two different things happen here:
selecting which rule fires (the shared tag/predicate expression language,
app/forms/visibility.py) and rendering the winning rule's text (recursive
{key} interpolation through the resolver, since rule text may itself
reference other placeholders - including other derived placeholders).
resolver.py calls into resolve_value() as step 0 of its precedence walk; this
module never resolves a whole document, only one derived key at a time.
"""
from app import db
from app.documents.models import DerivedPlaceholder
from app.documents.eligibility import build_eligibility_context, evaluate_expression

#: Rule text may reference other derived placeholders; resolution stops
#: rather than recursing forever once nesting goes this deep. Real templates
#: never approach this - it exists to turn a misconfigured cycle that
#: escaped setup-time validation into a bounded no-op instead of a
#: RecursionError during someone's document generation.
MAX_DERIVED_DEPTH = 8


def load_derived_placeholders(event_id):
    """{key: DerivedPlaceholder} for every active derived placeholder in an
    event. Called once per PlaceholderResolver, not per recipient - see
    resolver.py's PlaceholderResolver.__init__."""
    rows = (db.session.query(DerivedPlaceholder)
            .filter_by(event_id=event_id, is_active=True)
            .all())
    return {row.key: row for row in rows}


def _select_rule(derived_placeholder, eligibility_context):
    """The first rule (ascending `order`) whose condition holds - a None
    condition is the "otherwise" rule and always matches. None if nothing
    matched, which is a legitimate outcome distinct from matching empty text:
    the caller falls through to the next placeholder source rather than
    treating "no otherwise defined" as a resolved blank."""
    for rule in derived_placeholder.rules:
        if rule.condition_expression is None:
            return rule
        if evaluate_expression(rule.condition_expression, eligibility_context):
            return rule
    return None


def resolve_value(key, derived_placeholders, user, event, language,
                   condition_answer_fn, render_text_fn, chain=()):
    """Resolve one derived placeholder key for one recipient.

    Returns (value, matched):
      - matched=False: `key` isn't a derived placeholder, or it is but no
        rule fired (no condition matched and there is no "otherwise") - the
        caller (PlaceholderResolver._resolve_key) continues its precedence
        walk to the next source.
      - matched=True: a rule fired. `value` is that rule's text with every
        {key} occurrence inside it substituted - which may be an empty
        string, when the winning rule is an explicit "otherwise" with no
        text. That is a deliberate answer, not a gap, and downstream blank
        handling (allow_blank_values / |default) treats it identically to
        any other source's blank value.

    `condition_answer_fn(key) -> value_or_None` backs the `key`/`operator`
    leaf in rule conditions - deliberately NOT derived-placeholder-aware
    (design 5.7.5 scopes recursion to rule *text*, not conditions), so
    conditions can't participate in a cycle no matter how they're written.

    `render_text_fn(text, chain) -> str` renders {key} interpolation inside
    the winning rule's text, recursing back into this module for any nested
    derived placeholder it finds - see resolver.py's _render_derived_text.
    """
    derived_placeholder = derived_placeholders.get(key)
    if derived_placeholder is None:
        return None, False

    if key in chain or len(chain) >= MAX_DERIVED_DEPTH:
        # Primary cycle defence is validate_no_cycles() at save time; this is
        # a circuit breaker for whatever slips past it (e.g. a rule edited
        # directly against a stale cache of another admin's in-flight edit).
        return None, False

    eligibility_context = build_eligibility_context(
        user.id, event.id, answer_resolver=condition_answer_fn)

    rule = _select_rule(derived_placeholder, eligibility_context)
    if rule is None:
        return None, False

    translation = rule.get_translation(language) or rule.get_translation('en')
    text = translation.text if translation else ''
    rendered = render_text_fn(text, chain + (key,))
    return rendered, True


def referenced_keys(text):
    """Every {key} occurrence text interpolates, ignoring filters/namespace -
    used by validate_no_cycles to build the derived-placeholder dependency
    graph without evaluating anything."""
    from app.documents.resolver import extract_placeholder_occurrences, parse_placeholder
    keys = set()
    for raw in extract_placeholder_occurrences(text):
        namespace, key, _filters = parse_placeholder(raw)
        if namespace in (None, 'form'):
            keys.add(key)
    return keys


def find_cycle(event_id, changed_key=None, changed_rule_texts=None):
    """A dependency cycle among an event's derived placeholders, as a list of
    keys forming the loop, or None if there isn't one.

    Static analysis over rule text (which keys does each derived placeholder
    reference), not evaluation - a cycle is a property of the configuration,
    true for every recipient or none. `changed_key`/`changed_rule_texts` let
    the caller check a not-yet-committed edit (the admin UI validates before
    saving) by substituting its texts for that one key's edges.
    """
    placeholders = load_derived_placeholders(event_id)
    if changed_key is not None and changed_key not in placeholders:
        # A brand-new key: still a valid node other placeholders may
        # (harmlessly, until this save) already reference in their text, so
        # it must be in `placeholders` before any edge is computed - an
        # existing placeholder referencing it needs that edge to survive the
        # `refs & placeholders.keys()` intersection below.
        placeholders = dict(placeholders)
        placeholders[changed_key] = None

    all_keys = placeholders.keys()
    graph = {}
    for key, derived_placeholder in placeholders.items():
        if key == changed_key:
            continue
        refs = set()
        for rule in derived_placeholder.rules:
            translation = rule.get_translation('en') or (rule.translations[0] if rule.translations else None)
            if translation:
                refs |= referenced_keys(translation.text)
        # Intersected with the known placeholder keys, not with keys minus
        # itself - a rule that references its own placeholder is a
        # (degenerate, length-1) cycle and must stay detectable.
        graph[key] = refs & all_keys

    if changed_key is not None:
        refs = set()
        for text in (changed_rule_texts or []):
            refs |= referenced_keys(text)
        graph[changed_key] = refs & all_keys

    visiting, visited = set(), set()

    def dfs(node, path):
        if node in visiting:
            return path[path.index(node):] + [node]
        if node in visited:
            return None
        visiting.add(node)
        for neighbour in graph.get(node, ()):
            result = dfs(neighbour, path + [node])
            if result:
                return result
        visiting.discard(node)
        visited.add(node)
        return None

    for node in list(graph.keys()):
        if node not in visited:
            cycle = dfs(node, [])
            if cycle:
                return cycle
    return None

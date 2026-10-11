"""Liquid rendering for email templates.

A template is Markdown with Liquid tags. It is rendered three ways:

* ``html``    - every ``{{ }}`` output is escaped for HTML *and* Markdown, the
                result goes through Markdown and an nh3 allowlist, and buttons are
                swapped in last (see ``ButtonCollector``).
* ``text``    - no escaping; buttons render as ``Label: url``; Markdown syntax is
                stripped to readable plain text.
* ``subject`` - no escaping, no Markdown, newlines collapsed.

Templates only ever receive plain dicts, lists and scalars built by
``app.email_template.views``. Liquid resolves ``a.b`` with ``a["b"]`` and has no
attribute or method access on Python objects, so a template can't reach anything
a view model didn't put there.
"""
import html
import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import markdown as md_lib
import nh3
from liquid import Environment, Markup, StrictUndefined, Undefined
from liquid.builtin.expressions import FilteredExpression, parse_arguments
from liquid.builtin.output import Output, OutputNode
from liquid.builtin.tags.echo_tag import EchoNode, EchoTag
from liquid.exceptions import LiquidError, LiquidSyntaxError
from liquid.filter import with_context
from liquid.stringify import to_liquid_string
from liquid.tag import Tag
from liquid.token import TOKEN_TAG
from liquid.undefined import is_undefined
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


HTML, TEXT, SUBJECT, LAYOUT = 'html', 'text', 'subject', 'layout'

#: Keys the renderer puts in the context for its own tags and filters. They are
#: not valid Liquid identifiers, so a template can't name them with dot syntax.
LANGUAGE_KEY = '@language'
BUTTONS_KEY = '@buttons'

ALLOWED_URL_SCHEMES = ('http', 'https', 'mailto')

_FR_MONTHS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
              'septembre', 'octobre', 'novembre', 'décembre']
_FR_DAYS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
_EN_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
              'September', 'October', 'November', 'December']
_EN_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

DEFAULT_DATE_FORMAT = '%-d %B %Y'


class EmailRenderError(Exception):
    """A template could not be rendered. ``line`` and ``column`` are 1-based
    positions in the template source when Liquid reported one."""

    def __init__(self, message, line=None, column=None, field=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.field = field

    def to_dict(self):
        return {'message': self.message, 'line': self.line, 'column': self.column, 'field': self.field}


# --------------------------------------------------------------------------- escaping

# Characters Markdown would treat as syntax inside a substituted value. Python-
# Markdown turns a backslash before any of these back into the bare character
# ('|' only because the tables extension is enabled).
_MD_SPECIAL = re.compile(r'([\\`*_\[\]{}()#+\-!|])')


class MarkdownText(str):
    """Text that is itself Markdown (an admin's message), so it is substituted
    with its formatting intact. Raw HTML in it is still escaped."""

    def __html__(self):
        return html.escape(self, quote=False)


def escape_markdown(text):
    return _MD_SPECIAL.sub(r'\\\1', text)


class _HtmlOutputNode(OutputNode):
    """An output statement that escapes for Markdown on top of Liquid's HTML
    autoescape, so a value like ``*Bob*`` or ``[x](y)`` renders literally.
    Values already marked safe (``Markup``) are left alone."""

    def render_to_output(self, context, buffer):
        value = self.expression.evaluate(context)
        rendered = to_liquid_string(value, True)
        if not hasattr(value, '__html__'):
            rendered = Markup(escape_markdown(str(rendered)))
        return buffer.write(rendered)


class _HtmlOutput(Output):
    node_class = _HtmlOutputNode


class _HtmlEchoNode(_HtmlOutputNode, EchoNode):
    pass


class _HtmlEchoTag(EchoTag):
    node_class = _HtmlEchoNode


_TEXT_SPECIAL = re.compile(r'([\\`*_\[\]{}()#+\-!|<>])')


class _TextOutputNode(OutputNode):
    """Backslash-escapes a value's Markdown and HTML characters so that
    markdown_to_text, which strips both from the template, leaves the value as it
    was."""

    def render_to_output(self, context, buffer):
        value = self.expression.evaluate(context)
        rendered = to_liquid_string(value, False)
        if isinstance(value, MarkdownText):
            return buffer.write(rendered)
        return buffer.write(_TEXT_SPECIAL.sub(r'\\\1', rendered))


class _TextOutput(Output):
    node_class = _TextOutputNode


class _TextEchoNode(_TextOutputNode, EchoNode):
    pass


class _TextEchoTag(EchoTag):
    node_class = _TextEchoNode


# --------------------------------------------------------------------------- button tag

class ButtonCollector:
    """Holds the buttons a render produced, keyed by an unguessable token.

    The button tag writes a bare token into the Markdown, and the finished HTML
    has each token replaced by the button's table markup. The markup is generated
    here, so it never has to survive Markdown (which would wrap or mangle it) or
    the sanitiser (which would strip the inline styles email clients need).
    """

    def __init__(self, brand_colour):
        self.brand_colour = brand_colour
        self.nonce = uuid.uuid4().hex
        self.buttons = []

    def add(self, label, url, style):
        token = 'BTN{}N{}X'.format(self.nonce, len(self.buttons))
        self.buttons.append((token, label, url, style))
        return token

    def _button_html(self, label, url, style):
        colour = self.brand_colour
        if style == 'secondary':
            cell_style = 'border:2px solid {c};border-radius:6px;'.format(c=colour)
            link_style = ('display:inline-block;padding:10px 22px;font-weight:600;'
                          'color:{c};text-decoration:none;').format(c=colour)
        else:
            cell_style = 'background:{c};border-radius:6px;'.format(c=colour)
            link_style = ('display:inline-block;padding:12px 24px;font-weight:600;'
                          'color:#ffffff;text-decoration:none;')
        return ('<table role="presentation" cellspacing="0" cellpadding="0" border="0" '
                'style="margin:16px 0;"><tr><td style="{cell}">'
                '<a href="{url}" target="_blank" style="{link}">{label}</a>'
                '</td></tr></table>').format(
                    cell=cell_style, link=link_style,
                    url=html.escape(url, quote=True), label=html.escape(label))

    def substitute(self, html_text):
        for token, label, url, style in self.buttons:
            markup = self._button_html(label, url, style)
            # A button on a line of its own becomes its own paragraph; replace the
            # whole paragraph so the table isn't nested inside a <p>.
            html_text = html_text.replace('<p>{}</p>'.format(token), markup)
            html_text = html_text.replace(token, markup)
        return html_text


def check_url(url):
    url = (url or '').strip()
    scheme = url.split(':', 1)[0].lower() if ':' in url else ''
    if scheme not in ALLOWED_URL_SCHEMES:
        raise EmailRenderError(
            'Links must start with http://, https:// or mailto: (got "{}")'.format(url[:80]))
    return url


class ButtonNode(OutputNode):
    __slots__ = ('args', 'kwargs')

    def __init__(self, token, args, kwargs):
        super().__init__(token, None)
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return '{% button %}'

    def expressions(self):
        for arg in self.args:
            yield arg.value
        for kwarg in self.kwargs:
            yield kwarg.value

    def _evaluate(self, context):
        values = [arg.value.evaluate(context) for arg in self.args]
        options = {kwarg.name: kwarg.value.evaluate(context) for kwarg in self.kwargs}
        if len(values) != 2:
            raise LiquidSyntaxError('button expects a label and a link, e.g. '
                                    '{% button "Accept", offer.url %}', token=self.token)
        label, url = ['' if is_undefined(v) or v is None else str(v) for v in values]
        style = str(options.get('style') or 'primary')
        try:
            return label, check_url(url), style
        except EmailRenderError as e:
            raise LiquidError(e.message, token=self.token) from e

    def render_to_output(self, context, buffer):
        label, url, style = self._evaluate(context)
        collector = context.globals.get(BUTTONS_KEY)
        if collector is None:
            # Text and subject renders. In text, protect both parts from
            # markdown_to_text the way a substituted value is.
            if context.env.tags['output'].node_class is _TextOutputNode:
                label, url = (_TEXT_SPECIAL.sub(r'\\\1', part) for part in (label, url))
            return buffer.write('{}: {}'.format(label, url))
        return buffer.write(collector.add(label, url, style))


class ButtonTag(Tag):
    name = 'button'
    block = False
    node_class = ButtonNode

    def parse(self, stream):
        token = stream.eat(TOKEN_TAG)
        tokens = stream.into_inner(tag=token, eat=False)
        args, kwargs = parse_arguments(self.env, tokens)
        return self.node_class(token, args, kwargs)


# --------------------------------------------------------------------------- filters

def _language(context):
    language = context.globals.get(LANGUAGE_KEY) if context is not None else None
    return language if language in ('en', 'fr') else 'en'


def _as_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.rstrip('Z'))
        except ValueError:
            return None
    return None


def format_date(value, fmt=None, language='en'):
    """strftime with month and day names in the given language, independent of
    the server's locale."""
    moment = _as_datetime(value)
    if moment is None:
        return '' if value is None or is_undefined(value) else str(value)
    fmt = fmt or DEFAULT_DATE_FORMAT
    months, days = (_FR_MONTHS, _FR_DAYS) if language == 'fr' else (_EN_MONTHS, _EN_DAYS)
    fmt = (fmt.replace('%B', months[moment.month - 1])
              .replace('%A', days[moment.weekday()])
              .replace('%b', months[moment.month - 1][:3])
              .replace('%a', days[moment.weekday()][:3]))
    # %-d is a glibc extension; spell it out so the output doesn't depend on the platform.
    fmt = fmt.replace('%-d', str(moment.day))
    return moment.strftime(fmt)


@with_context
def date_filter(value, fmt=None, *, context):
    return format_date(value, fmt, _language(context))


def format_money(amount, currency='', language='en'):
    try:
        number = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return str(amount)
    text = '{:,.2f}'.format(number)
    if language == 'fr':
        text = text.replace(',', ' ').replace('.', ',')
    return '{} {}'.format(text, currency).strip()


@with_context
def money_filter(value, currency=None, *, context):
    """``{{ offer.fee | money }}`` for a fee/amount object, or
    ``{{ 1500 | money: "ZAR" }}`` for a bare number."""
    if isinstance(value, dict):
        return format_money(value.get('amount'), value.get('currency') or '', _language(context))
    if value is None or is_undefined(value):
        return ''
    return format_money(value, currency or '', _language(context))


@with_context
def list_filter(value, *, context):
    """Joins a list as prose: "A, B and C" / "A, B et C"."""
    if not isinstance(value, (list, tuple)):
        return '' if value is None or is_undefined(value) else str(value)
    items = [str(item) for item in value if item not in (None, '')]
    if len(items) <= 1:
        return ''.join(items)
    conjunction = ' et ' if _language(context) == 'fr' else ' and '
    return ', '.join(items[:-1]) + conjunction + items[-1]


# --------------------------------------------------------------------------- environments

class _EmailEnvironment(Environment):
    # Templates are written by event admins. These keep a careless or hostile
    # template from tying up a request worker.
    loop_iteration_limit = 10_000
    output_stream_limit = 1_000_000
    local_namespace_limit = 100_000
    context_depth_limit = 30


def _build_environment(mode, strict):
    env = _EmailEnvironment(
        autoescape=mode in (HTML, LAYOUT),
        undefined=StrictUndefined if strict else Undefined,
        strict_filters=True,
    )
    if mode == HTML:
        env.add_tag(_HtmlOutput)
        env.add_tag(_HtmlEchoTag)
    elif mode == TEXT:
        env.add_tag(_TextOutput)
        env.add_tag(_TextEchoTag)
    env.add_tag(ButtonTag)
    env.add_filter('date', date_filter)
    env.add_filter('money', money_filter)
    env.add_filter('list', list_filter)
    return env


_ENVIRONMENTS = {}


def environment(mode, strict=False):
    key = (mode, strict)
    if key not in _ENVIRONMENTS:
        _ENVIRONMENTS[key] = _build_environment(mode, strict)
    return _ENVIRONMENTS[key]


# --------------------------------------------------------------------------- errors

def _position(source, error):
    token = getattr(error, 'token', None)
    index = getattr(token, 'start_index', -1) if token is not None else -1
    if index is None or index < 0:
        return None, None
    before = source[:index]
    line = before.count('\n') + 1
    column = index - (before.rfind('\n') + 1) + 1
    return line, column


def _to_render_error(source, error, field):
    if isinstance(error, EmailRenderError):
        error.field = error.field or field
        return error
    line, column = _position(source, error)
    message = getattr(error, 'message', None) or str(error).split('\n')[0]
    return EmailRenderError(message, line=line, column=column, field=field)


def parse(source, mode=HTML, strict=False, field='body'):
    try:
        return environment(mode, strict).from_string(source or '')
    except LiquidError as e:
        raise _to_render_error(source or '', e, field) from e


def render_liquid(source, context, mode, language, strict=False, field='body', buttons=None):
    template = parse(source, mode, strict, field)
    globals_ = dict(context)
    globals_[LANGUAGE_KEY] = language
    if buttons is not None:
        globals_[BUTTONS_KEY] = buttons
    try:
        return template.render(**globals_)
    except (LiquidError, EmailRenderError) as e:
        raise _to_render_error(source or '', e, field) from e


# --------------------------------------------------------------------------- markdown

_URL_RE = re.compile(r'(?<![\w/"\'=])((?:https?://|mailto:)[^\s<>()]+[^\s<>().,;:!?\'"])')


class _LinkifyTreeprocessor(Treeprocessor):
    """Turns bare URLs in text into links. Python-Markdown only links URLs that
    are written as <https://...> or [text](url); in an email a bare URL is far
    more common, especially in templates converted from plain text."""

    def run(self, root):
        self._walk(root)

    def _walk(self, element):
        if element.tag in ('a', 'code', 'pre'):
            return
        children = list(element)
        if element.text:
            self._linkify_text(element, element.text, is_tail=False, anchor_index=0)
        for child in children:
            self._walk(child)
            if child.tail:
                self._linkify_text(element, child.tail, is_tail=True,
                                   anchor_index=list(element).index(child) + 1, previous=child)

    def _linkify_text(self, parent, text, is_tail, anchor_index, previous=None):
        import xml.etree.ElementTree as etree
        matches = list(_URL_RE.finditer(text))
        if not matches:
            return
        first_text = text[:matches[0].start()]
        if is_tail:
            previous.tail = first_text
        else:
            parent.text = first_text
        insert_at = anchor_index
        for i, match in enumerate(matches):
            link = etree.Element('a', {'href': match.group(1)})
            link.text = match.group(1)
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            link.tail = text[match.end():end]
            parent.insert(insert_at, link)
            insert_at += 1


class _LinkifyExtension(Extension):
    def extendMarkdown(self, md):
        # After 'unescape' (priority 0), so the text no longer holds Markdown's
        # escape placeholders.
        md.treeprocessors.register(_LinkifyTreeprocessor(md), 'email_linkify', -5)


def markdown_to_html(text):
    return md_lib.markdown(
        text or '',
        extensions=['nl2br', 'sane_lists', 'tables', _LinkifyExtension()],
        output_format='html',
    )


_ALLOWED_TAGS = {
    'a', 'b', 'blockquote', 'br', 'code', 'del', 'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5',
    'h6', 'hr', 'i', 'img', 'li', 'ol', 'p', 'pre', 's', 'small', 'span', 'strong', 'sub',
    'sup', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'u', 'ul',
}
_ALLOWED_ATTRIBUTES = {
    '*': {'style', 'align'},
    'a': {'href', 'title', 'target'},
    'img': {'src', 'alt', 'width', 'height'},
    'td': {'colspan', 'rowspan', 'width'},
    'th': {'colspan', 'rowspan', 'width'},
    'table': {'width', 'cellpadding', 'cellspacing', 'border', 'role'},
}


def sanitise_html(html_text):
    return nh3.clean(
        html_text,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=set(ALLOWED_URL_SCHEMES),
        link_rel='noopener noreferrer',
    )


_MD_LINK = re.compile(r'!?\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
_MD_EMPHASIS = re.compile(r'(\*\*|__)(.+?)\1|(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])')
_MD_HEADING = re.compile(r'^#{1,6}\s+', re.MULTILINE)
_MD_BLOCKQUOTE = re.compile(r'^>\s?', re.MULTILINE)
_MD_ESCAPED_CHAR = re.compile(r'\\([\\`*_\[\]{}()#+\-.!|<>])')
_HTML_TAG = re.compile(r'<script\b.*?</script\s*>|<style\b.*?</style\s*>|<[^>]+>',
                       re.IGNORECASE | re.DOTALL)
_PLACEHOLDER = re.compile('\x00(\\d+)\x00')


def markdown_to_text(text):
    """Markdown is already readable as plain text; this only drops the syntax
    (and any raw HTML) a reader would otherwise see literally.

    Backslash-escaped characters - which is how substituted values arrive, see
    _TextOutputNode - are set aside first so none of this touches them.
    """
    protected = []

    def protect(match):
        protected.append(match.group(1))
        return '\x00{}\x00'.format(len(protected) - 1)

    text = _MD_ESCAPED_CHAR.sub(protect, text or '')
    text = _HTML_TAG.sub('', text)
    text = _MD_LINK.sub(lambda m: m.group(1) if m.group(1) == m.group(2) or not m.group(1)
                        else '{} ({})'.format(m.group(1), m.group(2)), text)
    text = _MD_EMPHASIS.sub(lambda m: m.group(2) or m.group(3), text)
    text = _MD_HEADING.sub('', text)
    text = _MD_BLOCKQUOTE.sub('', text)
    text = html.unescape(text)
    text = _PLACEHOLDER.sub(lambda m: protected[int(m.group(1))], text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# --------------------------------------------------------------------------- whole fragments

def render_html_fragment(source, context, language, brand_colour, strict=False, field='body'):
    buttons = ButtonCollector(brand_colour)
    markdown_source = render_liquid(source, context, HTML, language, strict, field, buttons)
    return buttons.substitute(sanitise_html(markdown_to_html(markdown_source)))


def render_text_fragment(source, context, language, strict=False, field='body'):
    return markdown_to_text(render_liquid(source, context, TEXT, language, strict, field))


def render_subject(source, context, language, strict=False):
    rendered = render_liquid(source, context, SUBJECT, language, strict, field='subject')
    return ' '.join(rendered.split())[:500]


def plain_markdown_to_html(text):
    """Admin-authored Markdown with no Liquid (an announcement body)."""
    return sanitise_html(markdown_to_html(text))

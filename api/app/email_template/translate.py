"""Machine translation of an email template, keeping its Liquid and Markdown intact.

Sent as-is, a translation service would happily translate `{{ offer.url }}`,
`{% if %}` or `**`. So each line is turned into HTML before translating:

* every Liquid tag and output becomes `<span translate="no">N</span>` - Google
  Translate leaves those untouched - and is put back afterwards;
* a button's label is the one piece of Liquid that is prose, so it is pulled
  out of its tag and translated with the rest of the line;
* Markdown bold, italics and links become <b>, <i> and <a>, which the service
  moves around with the words they belong to; line prefixes (lists, headings,
  quotes) are kept aside and never sent.

A line whose placeholders don't all come back exactly once is left in the
source language rather than risk a broken template, and counted so the editor
can say so.
"""
import html
import re

from app.utils.translation import TranslationService


class TranslationUnavailable(Exception):
    pass


_LIQUID = re.compile(r'\{\{.*?\}\}|\{%.*?%\}', re.DOTALL)
_BUTTON = re.compile(r'^\{%-?\s*button\s+"([^"]*)"(.*?)-?%\}$', re.DOTALL)
_PREFIX = re.compile(r'^(\s*(?:[-*+]\s+|\d+\.\s+|#{1,6}\s+|>\s?)*)')
_LINK = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')
_BOLD = re.compile(r'\*\*(.+?)\*\*')
_ITALIC = re.compile(r'(?<![\w*])[*_](?!\s)(.+?)(?<!\s)[*_](?![\w*])')
_SPAN = re.compile(r'<span[^>]*>\s*(\d+)\s*</span>')


class _Line:
    def __init__(self, prefix, html_text, pieces, buttons, spacing):
        self.prefix = prefix
        # {piece: (had whitespace before, had whitespace after)}
        self.spacing = spacing
        self.html = html_text
        self.pieces = pieces
        # (opening piece, closing piece) around each button label.
        self.buttons = buttons


def _marker(index):
    return '\x00{}\x00'.format(index)


def _protect(line):
    """Split a line into (prefix, HTML to translate, protected pieces)."""
    prefix = _PREFIX.match(line).group(1)
    rest = line[len(prefix):]
    pieces = []
    buttons = []

    def hold(text):
        pieces.append(text)
        return _marker(len(pieces) - 1)

    def protect_liquid(match):
        tag = match.group(0)
        button = _BUTTON.match(tag)
        if button:
            # Only the label is prose; the rest of the tag is held back.
            opening, closing = hold('{% button "'), hold('"' + button.group(2) + '%}')
            buttons.append((len(pieces) - 2, len(pieces) - 1))
            return opening + button.group(1) + closing
        return hold(tag)

    rest = _LIQUID.sub(protect_liquid, rest)
    # Translation services pad the spans with spaces; remember where the
    # original had none so the result reads "salutation," not "salutation ,".
    spacing = {}
    for match in re.finditer('\x00(\\d+)\x00', rest):
        before = match.start() == 0 or rest[match.start() - 1].isspace()
        after = match.end() == len(rest) or rest[match.end()].isspace()
        spacing[int(match.group(1))] = (before, after)
    rest = html.escape(rest, quote=False)
    # The URL is held by index in a plain attribute: markup inside an
    # attribute wouldn't survive translation.
    rest = _LINK.sub(lambda m: '<a href="#{}">{}</a>'.format(
        hold(html.unescape(m.group(2)))[1:-1], m.group(1)), rest)
    rest = _BOLD.sub(r'<b>\1</b>', rest)
    rest = _ITALIC.sub(r'<i>\1</i>', rest)
    rest = re.sub('\x00(\\d+)\x00', r'<span translate="no">\1</span>', rest)
    return _Line(prefix, rest, pieces, buttons, spacing)


def _restore(line, translated):
    """The translated line as Markdown + Liquid, or None if any protected
    piece was lost or duplicated."""
    found = _SPAN.findall(translated) + re.findall(r'<a\s+href="#(\d+)"', translated)
    # Pieces held inside another piece (Liquid in a link URL) don't appear on their own.
    nested = {int(n) for piece in line.pieces for n in re.findall('\x00(\\d+)\x00', piece)}
    expected = [i for i in range(len(line.pieces)) if i not in nested]
    if sorted(int(n) for n in found) != expected:
        return None
    text = _SPAN.sub(lambda m: _marker(m.group(1)), translated)
    text = re.sub(r'<a\s+href="#(\d+)"\s*>(.*?)</a>',
                  lambda m: '[{}]({})'.format(m.group(2).strip(), _marker(m.group(1))), text)
    text = re.sub(r'<b>\s*(.*?)\s*</b>', r'**\1**', text)
    text = re.sub(r'<i>\s*(.*?)\s*</i>', r'_\1_', text)
    if '<' in re.sub(r'&lt;', '', text):
        return None  # Markup the service added or mangled; don't guess.
    text = html.unescape(text)

    for index, (before, after) in line.spacing.items():
        marker = re.escape(_marker(index))
        text = re.sub(r'[ \u00a0]+(?=' + marker + ')', ' ' if before else '', text)
        text = re.sub('(?<=' + marker + r')[ \u00a0]+', ' ' if after else '', text)

    for opening, closing in line.buttons:
        start, end = text.find(_marker(opening)), text.find(_marker(closing))
        if start < 0 or end < start:
            return None
        label_start = start + len(_marker(opening))
        # A translated label must not close the string literal early.
        text = text[:label_start] + text[label_start:end].strip().replace('"', "'") + text[end:]

    # Pieces can contain markers of their own (Liquid inside a link URL).
    while True:
        replaced = re.sub('\x00(\\d+)\x00', lambda m: line.pieces[int(m.group(1))], text)
        if replaced == text:
            return line.prefix + text
        text = replaced


def translate_template(text, source_language, target_language):
    """Returns (translated text, number of lines left untranslated)."""
    lines = (text or '').split('\n')
    work = []
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        # Nothing to translate: blank, or nothing but Liquid (a whole-line
        # tag). A button's label counts as text.
        prose = _LIQUID.sub(lambda m: _BUTTON.match(m.group(0)).group(1) if _BUTTON.match(m.group(0)) else '',
                            stripped)
        if not stripped or not prose.strip():
            continue
        work.append((index, _protect(raw)))

    if not work:
        return text, 0

    translated = TranslationService.translate_many(
        [line.html for _, line in work], target_language, source_language, format_='html')
    if translated is None or len(translated) != len(work):
        raise TranslationUnavailable('The translation service is not available right now.')

    kept = 0
    result = list(lines)
    for (index, line), output in zip(work, translated):
        restored = _restore(line, output)
        if restored is None:
            kept += 1
        else:
            result[index] = restored
    return '\n'.join(result), kept

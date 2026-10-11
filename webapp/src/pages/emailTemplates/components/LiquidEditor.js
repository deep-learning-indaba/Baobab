import React, { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { Annotation, EditorState, StateEffect, StateField } from '@codemirror/state';
import { Decoration, EditorView, keymap, placeholder as placeholderExtension } from '@codemirror/view';
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands';
import { autocompletion, completionKeymap } from '@codemirror/autocomplete';
import { defaultHighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { markdown } from '@codemirror/lang-markdown';
import { liquid } from '@codemirror/lang-liquid';
import { fieldAt, loopBindings } from './schema';

const CUSTOM_TAGS = [
  { label: 'button', type: 'keyword', detail: '"Label", link', apply: 'button "Label", ' },
];

const CUSTOM_FILTERS = [
  { label: 'date', type: 'function', detail: 'e.g. date: "%A %-d %B %Y"' },
  { label: 'money', type: 'function', detail: 'amount with currency' },
  { label: 'list', type: 'function', detail: '"A, B and C"' },
];

function completionsFor(fields) {
  return Object.entries(fields || {}).map(([name, field]) => ({
    label: name,
    type: field.type === 'object' || field.type === 'list' ? 'namespace' : 'property',
    detail: field.type,
    info: field.description,
  }));
}

// Marks a change made because `value` changed from outside, which isn't an edit.
const external = Annotation.define();

const setErrorLine = StateEffect.define();
const errorLineField = StateField.define({
  create: () => Decoration.none,
  update(decorations, transaction) {
    decorations = decorations.map(transaction.changes);
    for (const effect of transaction.effects) {
      if (effect.is(setErrorLine)) {
        const line = effect.value;
        if (!line || line > transaction.state.doc.lines) return Decoration.none;
        const from = transaction.state.doc.line(line).from;
        return Decoration.set([Decoration.line({ class: 'cm-error-line' }).range(from)]);
      }
    }
    return decorations;
  },
  provide: (field) => EditorView.decorations.from(field),
});

const theme = EditorView.theme({
  '&': { fontSize: '13px', backgroundColor: 'var(--color-surface, #fff)' },
  '.cm-content': { fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', padding: '10px 0' },
  '.cm-line': { padding: '0 12px' },
  '&.cm-focused': { outline: 'none' },
  '.cm-error-line': { backgroundColor: 'rgba(220, 38, 38, 0.10)' },
  '.cm-tooltip-autocomplete ul li[aria-selected]': { backgroundColor: '#0132c5', color: '#fff' },
});

/**
 * A CodeMirror editor for Markdown with Liquid tags. `schema` is the email
 * type's context ({ name: { fields, ... } }) - it drives autocompletion, so
 * typing `{{ offer.` lists the offer's fields, including inside a
 * `{% for grant in offer.grants %}` loop. The ref exposes insert(text) and
 * wrap(before, after) for the toolbar.
 */
const LiquidEditor = forwardRef(function LiquidEditor(
  { value, onChange, schema, singleLine = false, placeholder, ariaLabel, errorLine, minHeight = 320 },
  ref,
) {
  const hostRef = useRef(null);
  const viewRef = useRef(null);
  const schemaRef = useRef(schema);
  const onChangeRef = useRef(onChange);
  schemaRef.current = schema;
  onChangeRef.current = onChange;

  useEffect(() => {
    const properties = (path, state) => {
      const context = schemaRef.current || {};
      const bindings = loopBindings(state.doc.toString());
      const field = fieldAt(context, path, bindings);
      return field ? completionsFor(field.fields) : [];
    };

    const extensions = [
      history(),
      keymap.of([...defaultKeymap, ...historyKeymap, ...completionKeymap]),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      liquid({
        base: markdown(),
        tags: CUSTOM_TAGS,
        filters: CUSTOM_FILTERS,
        // Read once, when the editor is created - so it is only mounted once
        // the schema has loaded.
        variables: completionsFor(schemaRef.current || {}),
        properties,
      }),
      autocompletion(),
      errorLineField,
      theme,
      EditorView.lineWrapping,
      EditorView.contentAttributes.of({ 'aria-label': ariaLabel || '' }),
      EditorView.updateListener.of((update) => {
        const isExternal = update.transactions.some((tr) => tr.annotation(external));
        if (update.docChanged && !isExternal && onChangeRef.current) {
          onChangeRef.current(update.state.doc.toString());
        }
      }),
    ];
    if (placeholder) extensions.push(placeholderExtension(placeholder));
    if (singleLine) {
      extensions.push(EditorState.transactionFilter.of((tr) => (tr.newDoc.lines > 1 ? [] : tr)));
    } else {
      extensions.push(EditorView.theme({ '.cm-content, .cm-gutter': { minHeight: `${minHeight}px` } }));
    }

    const view = new EditorView({
      state: EditorState.create({ doc: value || '', extensions }),
      parent: hostRef.current,
    });
    viewRef.current = view;
    return () => view.destroy();
    // The editor is created once; value changes from outside are synced below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const view = viewRef.current;
    if (view && value !== view.state.doc.toString()) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: value || '' },
        annotations: external.of(true),
      });
    }
  }, [value]);

  useEffect(() => {
    const view = viewRef.current;
    if (view) view.dispatch({ effects: setErrorLine.of(errorLine || null) });
  }, [errorLine]);

  useImperativeHandle(ref, () => ({
    insert(text) {
      const view = viewRef.current;
      const { from, to } = view.state.selection.main;
      view.dispatch({
        changes: { from, to, insert: text },
        selection: { anchor: from + text.length },
        scrollIntoView: true,
      });
      view.focus();
    },
    wrap(before, after, fallback = '') {
      const view = viewRef.current;
      const { from, to } = view.state.selection.main;
      const selected = view.state.sliceDoc(from, to) || fallback;
      const text = before + selected + after;
      view.dispatch({
        changes: { from, to, insert: text },
        selection: { anchor: from + before.length, head: from + before.length + selected.length },
        scrollIntoView: true,
      });
      view.focus();
    },
    focus() {
      if (viewRef.current) viewRef.current.focus();
    },
  }));

  return (
    <div
      ref={hostRef}
      className={
        'rounded-lg border border-border bg-white overflow-hidden focus-within:ring-2 focus-within:ring-ring ' +
        (singleLine ? '' : 'min-w-0')
      }
    />
  );
});

export default LiquidEditor;

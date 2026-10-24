import { useEffect, useState } from 'react';
import { formServices } from '../../../services/form/form.service';

// Every DependencyEditor in the form, plus the linked-answers card, needs the
// linked form. Sharing one request per form id keeps that to a single fetch
// rather than one per question.
const cache = new Map();

/** Drop cached linked forms, so an editor opened later sees their latest structure. */
export function clearLinkedFormCache() {
  cache.clear();
}

function fetchLinkedForm(formId) {
  if (!cache.has(formId)) {
    const request = formServices.getForm(formId).then(response => {
      if (!response.form) throw new Error(response.error || 'Failed to load linked form');
      return response.form;
    });
    // A failed request isn't cached, so a later mount retries it.
    request.catch(() => cache.delete(formId));
    cache.set(formId, request);
  }
  return cache.get(formId);
}

/** The linked form's structure as { form, loading, error }. */
export default function useLinkedForm(linkedFormId) {
  const [state, setState] = useState({ form: null, loading: !!linkedFormId, error: null });

  useEffect(() => {
    if (!linkedFormId) {
      setState({ form: null, loading: false, error: null });
      return undefined;
    }
    let cancelled = false;
    setState(prev => ({ ...prev, loading: true, error: null }));
    fetchLinkedForm(linkedFormId).then(
      form => { if (!cancelled) setState({ form, loading: false, error: null }); },
      error => { if (!cancelled) setState({ form: null, loading: false, error }); }
    );
    return () => { cancelled = true; };
  }, [linkedFormId]);

  return state;
}

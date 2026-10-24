import React, { Suspense, lazy } from 'react';
import Loading from '../../components/Loading';

// Loaded on demand: the editor pulls in CodeMirror, which only admins editing
// emails need, so it stays out of the bundle every visitor downloads.
const withSuspense = (LazyComponent) => function EmailPage(props) {
  return (
    <Suspense fallback={<Loading />}>
      <LazyComponent {...props} />
    </Suspense>
  );
};

export const EmailTemplatesAdmin = withSuspense(lazy(() => import('./EmailTemplatesAdmin')));
export const EmailTemplateEditor = withSuspense(lazy(() => import('./EmailTemplateEditor')));
export const EmailLayoutEditor = withSuspense(lazy(() => import('./EmailLayoutEditor')));

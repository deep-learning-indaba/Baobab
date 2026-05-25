import React, { Component, Suspense } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { ErrorPage } from "./components/ErrorPage";
import { ErrorBoundary } from "react-error-boundary";
import i18nInit from './i18n';
import Loading from "./components/Loading";
import { organisationService } from "./services/organisation/organisation.service";
import ContextProvider from './context/ContextProvider';

// Retry lazy-loaded chunks to avoid stale-deploy chunk errors
const lazyRetry = function(componentImport) {
  return new Promise((resolve, reject) => {
      const hasRefreshed = JSON.parse(
          window.sessionStorage.getItem('retry-lazy-refreshed') || 'false'
      );
      componentImport().then((component) => {
          window.sessionStorage.setItem('retry-lazy-refreshed', 'false');
          resolve(component);
      }).catch((error) => {
          if (!hasRefreshed) {
              window.sessionStorage.setItem('retry-lazy-refreshed', 'true');
              return window.location.reload();
          }
          reject(error);
      });
  });
};

const App = React.lazy(() => lazyRetry(() => import('./App')));

class Bootstrap extends Component {
  constructor(props) {
    super(props);

    this.state = {
      organisation: null,
      loading: true
    };
  }

  componentDidMount() {
    organisationService.getOrganisation().then(response => {
      this.setState({
        organisation: response.organisation,
        error: response.error,
        loading: false
      });
      if (response.organisation) {
        document.title =
          response.organisation.system_name +
          " | " +
          response.organisation.name;
        i18nInit(response.organisation);
      }
    });
  }

  render() {
    if (this.state.loading) {
      return <Loading/>
    }

    return <Suspense fallback={<Loading />}>
      <App organisation={this.state.organisation}/>
    </Suspense>
  }
}

const root = createRoot(document.getElementById("root"));
root.render(
  <ErrorBoundary FallbackComponent={ErrorPage}>
    <ContextProvider>
      <Bootstrap />
    </ContextProvider>
  </ErrorBoundary>
);

import "react-app-polyfill/ie9";
import "array-flat-polyfill";
import React, { Component, Suspense } from "react";
import ReactDOM from "react-dom";
import "./index.css";
import * as serviceWorker from "./serviceWorker";
import { ErrorPage } from "./components/ErrorPage";
import { ErrorBoundary } from "react-error-boundary";
import i18nInit from './i18n';
import Loading from "./components/Loading";
import { organisationService } from "./services/organisation/organisation.service";
import ContextProvider from './context/ContextProvider';

// a function to retry loading a chunk to avoid chunk load error for out of date code
const lazyRetry = function(componentImport) {
  return new Promise((resolve, reject) => {
      // check if the window has already been refreshed
      const hasRefreshed = JSON.parse(
          window.sessionStorage.getItem('retry-lazy-refreshed') || 'false'
      );
      // try to import the component
      componentImport().then((component) => {
          window.sessionStorage.setItem('retry-lazy-refreshed', 'false'); // success so reset the refresh
          resolve(component);
      }).catch((error) => {
          if (!hasRefreshed) { // not been refreshed yet
              window.sessionStorage.setItem('retry-lazy-refreshed', 'true'); // we are now going to refresh
              return window.location.reload(); // refresh the page
          }
          reject(error); // Default error behaviour as already tried refresh
      });
  });
};


const App = React.lazy(() => lazyRetry(() => import('./App'))); // Lazy-loaded with retry

require("dotenv").config();

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

ReactDOM.render(
  <ErrorBoundary FallbackComponent={ErrorPage}>
    <ContextProvider>
      <Bootstrap />
    </ContextProvider>
  </ErrorBoundary>
  , document.getElementById("root")
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
serviceWorker.unregister();

import "react-app-polyfill/ie9";
import "array-flat-polyfill";
import React, { Component, Suspense } from "react";
import ReactDOM from "react-dom";
import "./index.css";
import * as serviceWorker from "./serviceWorker";
import { ErrorPage } from "./components/ErrorPage";
import { ErrorBoundary } from "react-error-boundary";
import i18nInit from "./i18n";
import Loading from "./components/Loading";
import { organisationService } from "./services/organisation/organisation.service";
import ContextProvider from "./context/ContextProvider";

const App = React.lazy(() => import("./App")); // Lazy-loaded

require("dotenv").config();

class Bootstrap extends Component {
  constructor(props) {
    super(props);

    this.state = {
      organisation: null,
      loading: true,
    };
  }

  componentDidMount() {
    organisationService.getOrganisation().then((response) => {
      this.setState({
        organisation: response.organisation,
        error: response.error,
        loading: false,
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
      return <Loading />;
    }

    return (
      <Suspense fallback={<Loading />}>
        <App organisation={this.state.organisation} />
      </Suspense>
    );
  }
}

ReactDOM.render(
  <ErrorBoundary FallbackComponent={ErrorPage}>
    <ContextProvider>
      <Bootstrap />
    </ContextProvider>
  </ErrorBoundary>,
  document.getElementById("root")
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
serviceWorker.unregister();

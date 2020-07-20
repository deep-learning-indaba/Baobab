import "react-app-polyfill/ie9";
import "array-flat-polyfill";
import React from "react";
import ReactDOM from "react-dom";
import Router from 'react-router-dom';
import "./index.css";
import App from "./App";
import * as serviceWorker from "./serviceWorker";
import { ErrorPage } from "./components/ErrorPage";
import { ErrorBoundary } from "react-error-boundary";
require("dotenv").config();

ReactDOM.render(
  <Router>
  <ErrorBoundary FallbackComponent={ErrorPage}>
    <App />
  </ErrorBoundary>
  </Router>,
  document.getElementById("root")
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
serviceWorker.unregister();

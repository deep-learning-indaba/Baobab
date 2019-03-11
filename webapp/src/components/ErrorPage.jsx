import { ErrorBoundary } from "react-error-boundary";
import logo from "../images/indaba-logo-dark.png";
import React from "react";
// Consider logging componentStack and error to string- stacktrace for components
export const ErrorPage = ({ componentStack, error }) => (
  <div className="Body">
    <div class="container h-100">
      <div class="row h-100 justify-content-center align-items-center" />
      <div>
        <img src={logo} className="img-fluid" alt="logo" />
      </div>
      <h2 className="Blurb">
        <strong>Oops! An error occured!</strong>
      </h2>
      <p>Here’s what we know.</p>
      <p>
        <strong>Error:</strong> {error.toString()}
      </p>
      <p>
        Please try again and if this issue persists contact
        baobab@deeplearningindaba.com with your error and username(if possible)
        as the Subject line.
      </p>
    </div>
  </div>
);

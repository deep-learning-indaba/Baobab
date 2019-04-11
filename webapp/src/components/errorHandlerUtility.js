// errorHandlerUtility.js
// import StackdriverErrorReporter from "stackdriver-errors-js";
import { StackdriverErrorReporter } from "stackdriver-errors-js";
import * as StackTrace from "stacktrace-js";
window.StackTrace = StackTrace;

const environment = process.env.NODE_ENV;

let errorHandler;

if (environment === "production") {
  errorHandler = new StackdriverErrorReporter();
  errorHandler.start({
    key: "xxx",
    projectId: "baobab"
  });
} else {
  errorHandler = { report: console.error };
}

export default errorHandler;

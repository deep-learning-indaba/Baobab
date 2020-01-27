import { StackdriverErrorReporter } from "stackdriver-errors-js";
import * as StackTrace from "stacktrace-js";
window.StackTrace = StackTrace;
const api_key = process.env.REACT_APP_STACKDRIVER_API_KEY || null;
const environment = process.env.NODE_ENV;

let errorHandler;
// TODO change Baobab to [event]
if (environment === "production") {
  if(api_key){
    errorHandler = new StackdriverErrorReporter();
    errorHandler.start({
      key: api_key,
      projectId: "baobab"
    });
  }
} else {
  errorHandler = { report: console.error };
}

export default errorHandler;

import React from "react";
import errorHandler from "../utils/errorHandlerUtility";

const BUG_SUBJECT_TEXT = "I encountered an bug in Baobab!";
const BUG_BODY_TEXT = `PLEASE ANSWER THE QUESTIONS BELOW. The more details you provide, 
the better the chance we can diagnose and fix the issue in a timely manner.

What is your browser name and version?
What page were you on when the error occured? 
What were you doing on the page?
What happened after that (the error)?

Error Message: 
`;

// Consider logging componentStack and error
export const ErrorPage = ({ componentStack, error }) => {
  if (errorHandler){
    var errorMessage= new Object();
    errorMessage.componentStack = componentStack;
    errorMessage.error  = error;
    var jsonString= JSON.stringify(errorMessage);
    errorHandler.report(jsonString);
  } 

  const bug_mailto =
    "mailto:baobab@deeplearningindaba.com?subject=" +
    encodeURI(BUG_SUBJECT_TEXT) +
    "&body=" +
    encodeURI(BUG_BODY_TEXT) +
    encodeURI(error.toString());

  return (
    <div className="Body">
      <div class="container h-100">
        <div class="row h-100 justify-content-center align-items-center" />
        <h2 className="Blurb">
          <strong>Oops! An error occured!</strong>
        </h2>
        <p>Here’s what we know.</p>
        <p>
          <strong>Error:</strong> {error.toString()}
        </p>
        <p>
        Please try again and if this issue persists, please{" "}
          <a href={bug_mailto}>get in touch</a> with us.<br/> The bug report will go to the Baobab team at the Deep Learning Indaba who maintain the application.
          <span style={{"font-weight": "bold"}}>Please answer the questions in the email in as much detail as possible before sending</span>. The more details you provide, the quicker we can diagnose and fix the issue.
        </p>
      </div>
    </div>
  );
};

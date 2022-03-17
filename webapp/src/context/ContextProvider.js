import React, { useState } from "react";
import AppContext from ".";

const ContextProvider = ({ children }) => {
  const [appFormData, setAppFormData] = useState(null);
  const context = {
    appFormData,
    setAppFormData,
  };
  return <AppContext.Provider value={context}>{children}</AppContext.Provider>;
};

export default ContextProvider;

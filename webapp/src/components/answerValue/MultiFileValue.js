import React from "react";

const baseUrl = process.env.REACT_APP_API_URL;

function MultiFileValue({value}) {
  const files = JSON.parse(value);
  return <ul>
    {files.map(v => 
      <li key={"file_" + v.id}>
        <a target="_blank" href={baseUrl + "/api/v1/file?filename=" + v.file}>
          {v.name}
        </a>
      </li>)}
  </ul>;
}

export default MultiFileValue;

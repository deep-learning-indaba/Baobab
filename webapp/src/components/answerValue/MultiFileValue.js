import React from "react";

import { getDownloadURL } from '../../utils/files';

function MultiFileValue({value}) {
  const files = JSON.parse(value);
  return <ul>
    {files.map(v => 
      <li key={"file_" + v.id}>
        <a target="_blank" href={getDownloadURL(v.file)}>
          {v.name}
        </a>
      </li>)}
  </ul>;
}

export default MultiFileValue;

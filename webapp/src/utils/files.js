/**
 * Generate applicable download URL from `value`
 * which can either be a plain or JSON string value.
 * @param   {String} value
 * @returns {String}
 */
export function getDownloadURL(value, bucketName) {
    const baseUrl = process.env.REACT_APP_API_URL;
    let url = baseUrl + "/api/v1/file?filename=";
    if (value) {
      try {
        const { filename, rename } = JSON.parse(value);
        url += filename + "&rename=" + encodeURIComponent(rename);
        if (bucketName) {
          url += "&bucket=" + bucketName;
        }
      } catch (e) {
        url += value;
      }
    }
    return url;
}

/**
 * Export CSV string as file.
 * @param {String} csv       String to be saved as CSV
 * @param {String} filename  Exported file's name
 */
export function downloadCSV(csv, filename) {
  const csvData = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  if (navigator.msSaveBlob) {
    navigator.msSaveBlob(csvData, filename);
  } else {
    var link = document.createElement('a');
    link.href = window.URL.createObjectURL(csvData);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

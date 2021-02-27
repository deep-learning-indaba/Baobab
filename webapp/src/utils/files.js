/**
 * Generate applicable download URL from `value`
 * which can either be a plain or JSON string value.
 * @param   {String} value
 * @returns {String}
 */
export function getDownloadURL(value) {
    const baseUrl = process.env.REACT_APP_API_URL;
    let url = baseUrl + "/api/v1/file?filename=";
    if (value) {
      try {
        const { filename, rename } = JSON.parse(value);
        url += filename + "&rename=" + encodeURIComponent(rename);
      } catch (e) {
        url += value;
      }
    }
    return url;
}

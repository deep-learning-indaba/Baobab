import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const fileService = {
  uploadFile,
};

function uploadFile(file, onUploadProgress) {
  var config = {
    onUploadProgress: onUploadProgress,
    headers: {
      ...authHeader(),
      "Content-Type": "multipart/form-data",
    },
  };

  let formData = new FormData();
  formData.append("file", file);

  return axios
    .post(baseUrl + "/api/v1/file", formData, config)
    .then((response) => {
      return {
        fileId: response.data.file_id,
        error: "",
      };
    })
    .catch((error) => {
      return {
        fileId: "",
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
      };
    });
}

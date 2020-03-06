import FormFileUpload from "./form/FormFileUpload";
import { fileService } from "../services/file/file.service";

export default class FileUploadComponent extends Component {
    constructor(props) {
      super(props);
      this.state = {
        uploadPercentComplete: 0,
        uploading: false,
        uploaded: false,
        uploadError: ""
      };
    }
  
    handleUploadFile = file => {
      this.setState({
        uploading: true
      }, () => {
        fileService
          .uploadFile(file, progressEvent => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total);
            this.setState({
              uploadPercentComplete: percentCompleted
            });
          })
          .then(response => {
            if (response.fileId && this.props.onChange) {
              this.props.onChange(this.props.question.id, response.fileId);
            }
            this.setState({
              uploaded: response.fileId !== "",
              uploadError: response.error,
              uploading: false
            });
          });
      }
      );
    };
  
    render() {
      return (
        <FormFileUpload
          Id={this.props.question.id}
          name={this.id}
          label={this.props.question.description}
          key={"i_" + this.props.key}
          value={(this.props.answer && this.props.answer.value) || ""}
          showError={this.props.validationError || this.state.uploadError}
          errorText={this.props.validationError || this.state.uploadError}
          uploading={this.state.uploading}
          uploadPercentComplete={this.state.uploadPercentComplete}
          uploadFile={this.handleUploadFile}
          uploaded={this.state.uploaded} />
      );
    }
  }
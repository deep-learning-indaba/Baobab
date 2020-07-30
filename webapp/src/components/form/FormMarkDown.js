// import react, react-markdown-editor-lite, and a markdown parser you like
import * as React from 'react'
import * as ReactDOM from 'react-dom'
import MarkdownIt from 'markdown-it'
import MdEditor from 'react-markdown-editor-lite'
import 'react-markdown-editor-lite/lib/index.css';
import { fileService } from '../../services/file/file.service'


const mdParser = new MarkdownIt();


class FormMarkDown extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      inputValue: ""
    }
  }


  handleEditorChange({ html, text }) {
    this.setState({
      inputValue: text
    })
  }

  onImageUpload(file) {
    return new Promise(resolve => {
      const reader = new FileReader();
      reader.onload = data => {

        this.uploadImg(file)
        resolve(data.target.result);
      };
      reader.readAsDataURL(file);
    });
  }

  uploadImg(file) {
    const baseUrl = process.env.REACT_APP_API_URL;

    return new Promise(resolve => {
      fileService.uploadFile(file).then(response => {
        resolve(response)
        console.log(`${baseUrl}/api/v1/file?filename=${response.fileId}`)
        return `${baseUrl}/api/v1/file?filename=${response.fileId}`

      })
    })
  }


  render() {
    return (
      <div className="formmarkdown-main-wrapper" >

        <MdEditor
          value={this.state.inputValue}
          style={{ height: "400px" }}
          renderHTML={(text) => mdParser.render(text)}
          onChange={(e) => this.handleEditorChange(e)}
          onImageUpload={(e) => this.onImageUpload(e)}
          config={{
            imageAccept: ['.png', '.jpg', '.gif']
          }}
        />

      </div>

    );
  }


}

export default FormMarkDown;


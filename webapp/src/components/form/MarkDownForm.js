import * as React from 'react'
import * as ReactDOM from 'react-dom'
import MarkdownIt from 'markdown-it'
import MdEditor from 'react-markdown-editor-lite'

import 'react-markdown-editor-lite/lib/index.css';


const mdParser = new MarkdownIt();

class MarkDownEditor extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            inputValue: ""
        }
    }
    

 handleEditorChange({html, text}) {    
  this.setState({
    inputValue: text
  })

  this.props.onChange({html, text})
}


 onImageUpload(file) {
    return new Promise(resolve => {
      const reader = new FileReader();
      reader.onload = data => {
        this.props.onImageUpload(file)
        resolve(data.target.result);
      };
      reader.readAsDataURL(file);
    })
  }


 render () {
    return (
        <MdEditor
          value={this.state.inputValue}
          style={{ height: "300px" }}
          renderHTML={(text) => mdParser.render(text)}
          onChange={(e) => this.handleEditorChange(e)}
          onImageUpload={(e) => this.onImageUpload(e)}
          config={{
            imageAccept: ['.png', '.jpg', '.gif']
          }}
          />
      )
 }

}

export default MarkDownEditor
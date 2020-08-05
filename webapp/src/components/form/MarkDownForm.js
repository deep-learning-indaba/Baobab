import React from 'react'
import MarkdownIt from 'markdown-it'
import MdEditor, { Plugins } from 'react-markdown-editor-lite'
import 'react-markdown-editor-lite/lib/index.css';

const mdParser = new MarkdownIt();
MdEditor.unuse(Plugins.FontUnderline);

 class MarkDownEditor extends React.Component {
       constructor(props) {
              super(props)
              this.state = {
                     inputValue: ""
              }
       }

       handleEditorChange({ text }) {
              
              this.setState({
                     inputValue: text
              })
              this.props.onChange(text)
       }

       onImageUpload(file) {
              return new Promise(resolve => {
                     const reader = new FileReader();
                     reader.onload = data => {
                            this.props.onImageUpload(file)
                            resolve(data.target.result)
                     };
                     reader.readAsDataURL(file);
              })
       }


       render() {
              return (
                     <div className="mark-down-form-wrapper">
                            <div id="md-editor" className={this.props.errorText && !this.props.value ? "select-control is-invalid" : "md-editor select-control"}>
                                   <MdEditor
                                          value={this.state.inputValue}
                                          style={{ height: "300px" }}
                                          renderHTML={(text) => mdParser.render(text)}
                                          onChange={(e) => this.handleEditorChange(e)}
                                          onImageUpload={(e) => this.onImageUpload(e)}
                                          config={{
                                                 imageAccept: ['.png', '.jpg', '.gif'],
                                                 imageUrl: 'image'
                                          }}
                                   />
                            </div>
                            <div className="invalid-feedback">{this.props.errorText}</div>
                     </div>
              )
       }
}

export default MarkDownEditor
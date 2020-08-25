import React, { Component } from "react";
import MarkdownIt from 'markdown-it'
import MdEditor from 'react-markdown-editor-lite'
import Editor, { Plugins } from 'react-markdown-editor-lite';
import 'react-markdown-editor-lite/lib/index.css';

// Remove underline from React Markdown Editor Lite because MarkdownIt doesn't render it.
Editor.unuse(Plugins.FontUnderline);


const mdParser = new MarkdownIt();


class MarkDownEditor extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            inputValue: ""
        }
    }
    

 handleEditorChange({text}) {    
  this.setState({
    inputValue: text
  })

  this.props.onChange(text)
}


 onImageUpload(file) {
    return this.props.onImageUpload(file);
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
            imageAccept: ['.png', '.jpg', '.gif'],
            view: { menu: true, md: true }
          }}
          />
      )
 }

}

export default MarkDownEditor

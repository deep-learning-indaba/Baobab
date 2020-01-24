import React from 'react';
import {EditorState, Modifier} from "draft-js";
import {Editor} from "react-draft-wysiwyg";
import './RichText.css';

class EditorContainer extends React.Component{
  constructor(props){
    super(props);
    this.state = {
      editorState: EditorState.createEmpty(),
    };
  }
  onEditorStateChange = (editorState) => {
    // console.log(editorState)
    this.setState({
      editorState,
    });
  };
  handleKeyCommand = (command) => {

    if (command == 'backspace' || command == 'delete') {
        command = ''
    }
    const editorState = this.state.editorState;
    const currentState = editorState.getCurrentContent();  //get current text content
    const selection = editorState.getSelection();
    let contentState;
    if (selection.isCollapsed()) {
        contentState = Modifier.insertText(currentState, selection, command);
    }
    else {
        contentState = Modifier.replaceText(currentState, selection, "");
    }
    this.setState({ editorState: EditorState.push(this.state.editorState, contentState, 'insert-fragment') });

}
  render(){
    const { editorState } = this.state;
    return <div className='editor'>
      <Editor
        editorState={editorState}
        onEditorStateChange={this.onEditorStateChange} 
        handleKeyCommand={this.handleKeyCommand}   
        toolbar={{
          inline: { inDropdown: true },
          list: { inDropdown: true },
          textAlign: { inDropdown: true },
          link: { inDropdown: true },        
        }}
      />
    </div>
  }
}

const FormRichText = () => (
    <div>
      <EditorContainer />
    </div>
  );

export default FormRichText;

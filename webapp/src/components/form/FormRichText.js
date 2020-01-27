import React from 'react';
import { EditorState, Modifier } from "draft-js";
import { Editor } from "react-draft-wysiwyg";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import './RichText.css';

class EditorContainer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      editorState: EditorState.createEmpty(),
    };
  }

  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  getWordCount = () => {
    const stringToCount = this.state.editorState.getCurrentContent().getPlainText();
    let wordCount = stringToCount.trim().split(/\s+/).length;
    return wordCount;
}

onEditorStateChange = (editorState) => {
  this.setState({
    editorState,
  });
};
handleKeyCommand = (command) => {

  if (command == 'backspace' || command == 'delete') {
    command = ''
  }
  const editorState = this.state.editorState;
  const currentState = editorState.getCurrentContent();
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
render() {
  const { editorState } = this.state;
  return <div className='editor'>
    <FormGroup
      id={this.props.Id + "-group"}
      errorText={this.props.errorText}
    >
      <div className="rowC">
        <label htmlFor={this.props.id}>{this.props.label}</label>
        {this.props.description ? (
          <FormToolTip description={this.props.description} />
        ) : (
            <div />
          )}
      </div>
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
        id={this.props.Id}
        className={
          this.shouldDisplayError()
            ? "form-control is-invalid"
            : "form-control"
        }
        type={this.props.type || "text"}
        placeholder={this.props.placeholder}
        value={this.props.value}
        onChange={this.props.onChange}
        min={this.props.min || null}
        ref={input => {
          this.nameInput = input;
        }}
        tabIndex={this.props.tabIndex}
        autoFocus={this.props.autoFocus}
        required={this.props.required || null}
      />
      <span class="question__word-count float-right">Word Count:{this.getWordCount()}</span>
    </FormGroup>
  </div>
}
}
const FormRichText = () => (
  <div>
    <EditorContainer
    />
  </div>
);
export default FormRichText;

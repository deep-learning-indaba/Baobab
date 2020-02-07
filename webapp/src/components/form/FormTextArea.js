import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";

class FormTextArea extends React.Component {
  state = {
    words: 0,
    characters: 0,
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
    let words = 0;
    if (this.props.value) {
      words = this.props.value.trim().split(/\s+/).length;
    } else {
      words = 0;
    }

    this.setState({
      words
    })
    return words
  };

  render() {
    return (
      <div>
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
          <textarea
            id={this.props.Id}
            className={
              this.shouldDisplayError()
                ? "form-control is-invalid"
                : "form-control"
            }
            placeholder={this.props.placeholder}
            rows={this.props.rows}
            value={this.props.value || ""}
            onChange={this.props.onChange}
            onKeyPress={this.getWordCount}
            onKeyUp={this.getWordCount}
            ref={input => {
              this.nameInput = input;
            }}
            key={"text_"+this.props.key}
            tabIndex={this.props.tabIndex}
            autoFocus={this.props.autoFocus}
          />
          <span class="question__word-count float-right">Word Count:{this.state.words}</span>
        </FormGroup>
        
      </div>
    );
  }
}

export default FormTextArea;

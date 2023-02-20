import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import { withTranslation } from 'react-i18next';
import MarkdownRenderer from "../MarkdownRenderer";

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
    this.getWordCount();
  }

  componentDidMount() {
    this.getWordCount();
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
    const t = this.props.t;
    
    return (
      <div>
        <div className="rowC">
          <MarkdownRenderer source={this.props.label}/>
          {this.props.description ? (
            <FormToolTip description={this.props.description} />
          ) : (
            <div />
          )}
        </div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          <textarea
            id={this.props.id}
            className={
              this.shouldDisplayError()
                ? "form-control is-invalid"
                : "form-control"
            }
            placeholder={this.props.placeholder}
            rows={this.props.rows}
            value={this.props.value || ""}
            onChange={this.props.onChange}
            onKeyDown={this.getWordCount}
            onKeyUp={this.getWordCount}
            onMouseUp={this.getWordCount}
            onMouseDown={this.getWordCount}
            ref={input => {
              this.nameInput = input;
            }}
            key={"text_"+this.props.key}
            tabIndex={this.props.tabIndex}
            autoFocus={this.props.autoFocus}
          />
          <span className="question__word-count float-right">{t('Word Count') + ': ' + this.state.words}</span>
        </FormGroup>
        
      </div>
    );
  }
}

export default withTranslation()(FormTextArea);

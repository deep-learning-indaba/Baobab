import React, { Component } from "react";
import FormGroup from "./FormGroup";
import ReactToolTip from "react-tooltip";
import FormToolTip from "./FormToolTip";

class FormTextArea extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  getWordCount = () => {
    if (this.props.value) {
      return this.props.value.split(" ").filter(value => value !== "").length;
    } else {
      return 0;
    }
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
            value={this.props.value}
            onChange={this.props.onChange}
            ref={input => {
              this.nameInput = input;
            }}
            tabIndex={this.props.tabIndex}
            autoFocus={this.props.autoFocus}
          />
        </FormGroup>
        <p class="question__word-count">Word Count:{this.getWordCount()}</p>
      </div>
    );
  }
}

export default FormTextArea;

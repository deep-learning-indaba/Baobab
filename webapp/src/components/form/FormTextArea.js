import React, { Component } from "react";
import FormGroup from "./FormGroup";
import ReactToolTip from "react-tooltip";
import FormToolTip from "./FormToolTip";
import "./Style.css";

class FormTextArea extends React.Component {
<<<<<<< HEAD
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
=======
    shouldDisplayError = () => {
      return this.props.showError && this.props.errorText !== ""
    }
  
    componentWillReceiveProps(nextProps) {
      if (nextProps.showFocus) {
        this.nameInput.focus()
      }
    }

    getWordCount = () => {
      if (this.props.value) {
        return this.props.value.split(" ").filter(value => (value!== "")).length;
      }
      else {
        return 0;
      }
    }
    render() {
      return (
        <div>
          <FormGroup
            id={this.props.Id + "-group"}
            errorText={this.props.errorText}
          >
            <label data-tip={this.props.description}  htmlFor={this.props.Id}>
              {this.props.label}
            </label>
            <ReactToolTip />
            <textarea
              id={this.props.Id}
              className={this.shouldDisplayError() ? "form-control is-invalid" : "form-control"}
              placeholder={this.props.placeholder}
              rows={this.props.rows} 
              value={this.props.value}
              onChange={this.props.onChange}
              ref={input => {
                this.nameInput = input
              }}
              tabIndex={this.props.tabIndex}
              autoFocus={this.props.autoFocus}
            ></textarea>
          </FormGroup>
          <p class="question__word-count">Word Count:{this.getWordCount()}</p>
        </div>
      )
>>>>>>> develop
    }
  }
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
      </div>
    );
  }
}

export default FormTextArea;

import React, { Component } from "react";
import ReactToolTip from "react-tooltip";
import FormGroup from "./FormGroup";

class FormTextBox extends React.Component {
    shouldDisplayError = () => {
      return this.props.showError && this.props.errorText !== ""
    }
  
    componentWillReceiveProps(nextProps) {
      if (nextProps.showFocus) {
        this.nameInput.focus()
      }
    }
    render() {
      return (
        <div>
          <FormGroup
            id={this.props.Id + "-group"}
            showError={this.shouldDisplayError()}
            errorText={this.props.errorText}
          >
            <label data-tip={this.props.description} htmlFor={this.props.Id}>
              {this.props.label}
            </label>
            <ReactToolTip/>
            <input
              id={this.props.Id}
              className={"form-control"}
              type={this.props.type || "text"}
              placeholder={this.props.placeholder}
              value={this.props.value}
              onChange={this.props.onChange}
              min={this.props.min || null}
              ref={input => {
                this.nameInput = input
              }}
              tabIndex={this.props.tabIndex}
              autoFocus={this.props.autoFocus}
            />
          </FormGroup>
        </div>
      )
    }
  }
  export default FormTextBox
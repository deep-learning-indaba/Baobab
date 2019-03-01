import React, { Component } from "react";
import FormGroup from "./FormGroup";
import { default as ReactSelect } from "react-select";
import ReactToolTip from "react-tooltip";

class FormSelect extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }
  render() {
    const { id, options, placeholder, onChange } = this.props;
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          <label data-tip={this.props.description} htmlFor={this.props.id}>{this.props.label}</label>
          <ReactToolTip />
          <ReactSelect
            id={id}
            options={options}
            placeholder={placeholder}
            onChange={e => onChange(id, e)}
          />
        </FormGroup>
      </div>
    );
  }
}
export default FormSelect;

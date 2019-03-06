import React, { Component } from "react";
import FormGroup from "./FormGroup";
import { default as ReactSelect } from "react-select";
import ReactToolTip from "react-tooltip";
import FormToolTip from "./FormToolTip";
import "./Style.css";

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
    const { id, options, placeholder, onChange, defaultValue } = this.props;
    let value = this.props.value;
    if (defaultValue) {
      value = options.filter(option => option.value === defaultValue);
    }
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          <label htmlFor={this.props.id}>{this.props.label}</label>
          <div className="rowC">
            <FormToolTip description={this.props.description} />
          </div>
          <ReactSelect
            id={id}
            options={options}
            placeholder={placeholder}
            value={value}
            onChange={e => onChange(id, e)}
            defaultValue={value || null}
            className={
              this.shouldDisplayError()
                ? "select-control is-invalid"
                : "select-control"
            }
          />
        </FormGroup>
      </div>
    );
  }
}
export default FormSelect;

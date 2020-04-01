import React from "react";
import DateTimePicker from 'react-datetime-picker'
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";

class FormDate extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.dateInput.focus();
    }
  }

  onChange = value => {
    if (value && this.props.onChange) {
      this.props.onChange(value.toISOString());
    }
  }

  render() {
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
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

        <DateTimePicker
          id={this.props.id}
          ref={input => {
            this.dateInput = input;
          }}
          onChange={this.onChange}
          value={Date.parse(this.props.value)}
          required={this.props.required || null}
          tabIndex={this.props.tabIndex}
          autoFocus={this.props.autoFocus}
          format="y-MM-dd"
        />
        </FormGroup>
      </div>
    );
  }
}
export default FormDate;

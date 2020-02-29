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

        <DateTimePicker
          id={this.props.Id}
          className={
            this.shouldDisplayError()
                ? "form-control is-invalid"
                : "form-control"
          }
          ref={input => {
            this.dateInput = input;
          }}
          onChange={this.props.onChange}
          value={this.props.value}
          required={this.props.required || null}
          tabIndex={this.props.tabIndex}
          autoFocus={this.props.autoFocus}
        />
        </FormGroup>
      </div>
    );
  }
}
export default FormDate;

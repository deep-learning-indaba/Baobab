import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";

class FormTextBox extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
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
            <label htmlFor={this.props.id} className={
              (this.props.isDisabled
                ? " disabled-form-control"
                : "")
            }>{this.props.label}</label>
            {this.props.description ? (
              <FormToolTip description={this.props.description} />
            ) : (
                <div />
              )}
          </div>
          <input
            id={this.props.id}
            className={
              "form-control"
              + (this.shouldDisplayError()
                ? " is-invalid"
                : "")
              + (this.props.isDisabled
                ? " disabled-form-control"
                : "")
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
        </FormGroup>
      </div>
    );
  }
}
export default FormTextBox;

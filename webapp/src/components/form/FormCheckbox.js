import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";

class FormCheckbox extends React.Component {
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
          <input
            id={this.props.Id}
            className={
              this.shouldDisplayError()
                ? "form-control is-invalid"
                : "form-control"
            }
            type="checkbox"
            placeholder={this.props.placeholder}
            checked={this.props.value}
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
export default FormCheckbox;

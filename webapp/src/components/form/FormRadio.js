import React from "react";
import FormGroup from "./FormGroup";
import "./Style.css";

class FormRadio extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  render() {
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
            {this.props.label && <div className="rowC">
                <p>{this.props.label}</p>
            </div>}
            {this.props.options.map(o=>{
                return (
                    <div className={"form-check form-check-inline " + (this.shouldDisplayError() ? "is-invalid" : "")} key={this.props.id + "_" + o.value}>
                        <input
                            id={this.props.id + "_" + o.value}
                            name={this.props.id}
                            className={
                            this.shouldDisplayError()
                                ? "form-check-input is-invalid"
                                : "form-check-input"
                            }
                            type="radio"
                            value={o.value}
                            checked={this.props.value === o.value}
                            onChange={this.props.onChange}
                            tabIndex={this.props.tabIndex}
                            autoFocus={this.props.autoFocus}
                        />
                        <label class="form-check-label" htmlFor={this.props.id + "_" + o.value}>{o.label}</label>
                    </div>
                );
            })}
        </FormGroup>
      </div>
    );
  }
}
export default FormRadio;

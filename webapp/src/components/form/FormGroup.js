import React, { Component } from "react";
class FormGroup extends React.Component {
  render() {
    let formClass = this.props.showError ? "form-group error" : "form-group";
    if (this.props.isCheckBox) formClass = "form-group";

    return (
      <div>
        <div id={this.props.id} className={formClass}>
          {this.props.children}
        </div>
        {this.props.showError ? (
          <p className="error-text">{this.props.errorText}</p>
        ) : (
          ""
        )}
      </div>
    );
  }
}

export default FormGroup;

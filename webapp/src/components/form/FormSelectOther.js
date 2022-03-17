/* Wraps a FormMultiCheckbox, adding an "other" option */

import React from "react";
import "./Style.css";
import FormSelect from "./FormSelect";
import { withTranslation } from "react-i18next";

class FormSelectOther extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      options: [],
      value: [],
      showOther: false,
      otherText: "",
    };
  }

  componentDidMount() {
    const options = this.props.options;
    if (!options.some((o) => o.value === "other")) {
      options.push({
        value: "other",
        label: this.props.t("Other") + "...",
      });
    }

    let otherText = "";
    let showOther = false;
    if (
      this.props.defaultValue &&
      !options.some((o) => o.value === this.props.defaultValue)
    ) {
      otherText = this.props.defaultValue;
      showOther = true;
    }

    this.setState({
      options: options,
      otherText: otherText,
      showOther: showOther,
    });
  }

  getDefaultValue = () => {
    let defaultValue = this.props.defaultValue;
    if (
      this.props.defaultValue &&
      !this.props.options.some((o) => o.value === this.props.defaultValue)
    ) {
      defaultValue = "other";
    }
    return defaultValue;
  };

  notifyValueChanged = () => {
    const value = this.state.showOther
      ? this.state.otherText
      : this.state.value;
    if (this.props.onChange) {
      this.props.onChange(value);
    }
  };

  onChange = (_, dropdown) => {
    const value = dropdown.value.toString();
    this.setState(
      {
        showOther: value === "other",
        value: value,
      },
      () => {
        this.notifyValueChanged();
      }
    );
  };

  onOtherChanged = (e) => {
    this.setState(
      {
        otherText: e.target.value,
      },
      () => {
        this.notifyValueChanged();
      }
    );
  };

  render() {
    const t = this.props.t;
    return (
      <div>
        <FormSelect
          options={this.state.options}
          id={this.props.id}
          name={this.props.name}
          onChange={this.onChange}
          defaultValue={this.getDefaultValue()}
          placeholder={this.props.placeholder}
          label={this.props.label}
          required={this.props.required}
          key={this.props.id}
          showError={this.props.showError}
          errorText={this.props.errorText}
        />
        {this.state.showOther && (
          <div class="form-group row">
            <label
              for={this.props.id + "_other"}
              class="col-sm-2 col-form-label"
            >
              {t("Other - Please Specify")}:
            </label>
            <div class="col-sm-10">
              <input
                type="text"
                className="form-control"
                id={this.props.id + "_other"}
                onChange={this.onOtherChanged}
                value={this.state.otherText}
                key={"key_" + this.props.id}
              />
            </div>
          </div>
        )}
      </div>
    );
  }
}

export default withTranslation()(FormSelectOther);

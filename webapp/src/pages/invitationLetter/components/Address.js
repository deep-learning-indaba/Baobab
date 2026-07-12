// TODO: ADD TRANSLATION
import React, { Component } from "react";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { getCountries } from "../../../utils/validation/contentHelpers";

class Address extends Component {
  constructor(props) {
    super(props);

    this.state = {
      countryOptions: []
    };
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList;
    } else
      return [];
  }

  componentDidMount() {
    getCountries.then(result => {
      this.setState({
        countryOptions: this.checkOptionsList(result)
      });
    });
  }

  render() {
    const {
      streetAddress1,
      streetAddress2,
      city,
      postalCode,
      country,
      streetAddress1Value,
      streetAddress2Value,
      cityValue,
      postalCodeValue,
      countryValue
    } = this.props;

    return (
      <div className="space-y-4 p-6 bg-surface-low rounded-xl border border-border">
        <div>
          <FormTextBox
            id={streetAddress1.name}
            type="text"
            placeholder={streetAddress1.display}
            onChange={this.props.onChange(streetAddress1)}
            value={streetAddress1Value}
            label={streetAddress1.display} />
        </div>

        <div>
          <FormTextBox
            id={streetAddress2.name}
            type="text"
            placeholder={streetAddress2.display}
            onChange={this.props.onChange(streetAddress2)}
            value={streetAddress2Value}
            label={streetAddress2.display} />
        </div>

        <div>
          <FormTextBox
            id={city.name}
            type="text"
            placeholder={city.display}
            onChange={this.props.onChange(city)}
            value={cityValue}
            label={city.display} />
        </div>

        <div>
          <FormTextBox
            id={postalCode.name}
            type="text"
            placeholder={postalCode.display}
            onChange={this.props.onChange(postalCode)}
            value={postalCodeValue}
            label={postalCode.display} />
        </div>

        <FormSelect
          options={this.state.countryOptions}
          id={country.name}
          placeholder={country.display}
          onChange={this.props.handleChangeDropdown}
          value={countryValue}
          label={country.display} />
      </div>
    );
  }
}

export default Address;

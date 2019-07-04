import React, { Component } from "react";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { createColClassName } from "../../../utils/styling/styling";
import validationFields from "../../../utils/validation/validationFields";
import { getCounties } from "../../../utils/validation/contentHelpers";
class Address extends Component {
  constructor(props) {
    super(props);

    this.state = {
      streetAddress1: props.streetAddress1,
      streetAddress2: props.streetAddress2,
      city: props.city,
      postalCode: props.postalCode,
      country: props.country,
      countryOptions: [],
      addressText: {
        streetAddress1Value: props.streetAddress1Value,
        streetAddress2Value: props.streetAddress2Value,
        cityValue: props.cityValue,
        postalCodeValue: props.postalCodeValue,
        countryValue: props.countryValue
      }
    };
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList;
    } else return [];
  }
  componentWillMount() {
    getCounties.then(result => {
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
      country
    } = this.state;
    const {
      streetAddress1Value,
      streetAddress2Value,
      cityValue,
      postalCodeValue,
      countryValue
    } = this.state.addressText;
    const addressStyle = createColClassName(12, 4, 6, 6);
    return (
      <div class={addressStyle}>
        <div>
          <FormTextBox
            id={streetAddress1.name}
            type="text"
            placeholder={streetAddress1.display}
            onChange={this.props.onChange(streetAddress1)}
            value={streetAddress1Value}
            label={streetAddress1.display}
          />
        </div>
        <div>
          <FormTextBox
            id={streetAddress2.name}
            type="text"
            placeholder={streetAddress2.display}
            onChange={this.props.onChange(streetAddress2)}
            value={streetAddress2Value}
            label={streetAddress2.display}
          />
        </div>
        <div>
          <FormTextBox
            id={city.name}
            type="text"
            placeholder={city.display}
            onChange={this.props.onChange(city)}
            value={cityValue}
            label={city.display}
          />
        </div>
        <div>
          <FormTextBox
            id={postalCode.name}
            type="text"
            placeholder={postalCode.display}
            onChange={this.props.onChange(postalCode)}
            value={postalCodeValue}
            label={postalCode.display}
          />
        </div>
        <FormSelect
          options={this.state.countryOptions}
          id={country.name}
          placeholder={country.display}
          onChange={this.props.handleChangeDropdown}
          value={countryValue}
          label={country.display}
        />
      </div>
    );
  }
}

export default Address;

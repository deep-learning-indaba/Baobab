/* Wraps a FormMultiCheckbox, adding an "other" option */

import React from "react";
import "./Style.css";
import _ from "lodash";
import FormMultiCheckbox from "./FormMultiCheckbox";

class FormMultiCheckboxOther extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            options: [],
            values: [],
            showOther: false,
            otherText: "",
        };
    }

    getDefaultValues = () => {
        let defaultValues = this.props.defaultValue.split(' ; ');
        const otherValue = _.find(defaultValues, v => !this.props.options.some(o => o.value === v));
        if (otherValue) {
            defaultValues = defaultValues.filter(v => v !== otherValue);
            defaultValues.push('other');
        }
        return {
            defaultValues: defaultValues,
            otherValue: otherValue
        };
    }

    componentDidMount() {
        const options = this.props.options;
        if (!options.some(o => o.value === "other")) {
            options.push({
                'value': 'other',
                'label': 'Other...'
            });
        }

        const defaultValues = this.getDefaultValues();
        if (defaultValues.defaultValues.some(d => d === "other")) {
            this.setState({
                showOther: true,
                otherText: defaultValues.otherValue
            });
        }


        this.setState({
            options: options,
        });
    }

    notifyValueChanged = () => {
        const values = this.state.values.filter(v => v !== "other");
        if (this.state.showOther) {
            values.push(this.state.otherText);
        }
        if (this.props.onChange) {
            this.props.onChange(values.join(' ; '));
        }
    }

    onChange = (value) => {
        let values = value.split(' ; ');

        this.setState({
            showOther: values.some(v => v === "other"),
            values: values
        }, () => {
            this.notifyValueChanged();
        });
    }

    onOtherChanged = e => {
        this.setState({
            otherText: e.target.value.replace(";", "")
        }, () => { this.notifyValueChanged(); });
    }

    render() {
        return <div>

            <FormMultiCheckbox
                id={this.props.id}
                name={this.props.id}
                options={this.state.options}
                onChange={this.onChange}
                key={this.props.id}
                showError={this.props.showError}
                errorText={this.props.errorText}
                defaultValue={this.getDefaultValues().defaultValues.join(' ; ')}
            />
            {this.state.showOther &&
                <div class="form-group row">
                    <label for="inputPassword" class="col-sm-2 col-form-label">Other - Please Specify:</label>
                    <div class="col-sm-10">
                        <input
                            type="text"
                            class="form-control"
                            id={this.props.id + '_other'}
                            onChange={this.onOtherChanged}
                            key={'key_' + this.props.id}
                            value={this.state.otherText}
                        />
                    </div>
                </div>}
        </div>
    }

}

export default FormMultiCheckboxOther;

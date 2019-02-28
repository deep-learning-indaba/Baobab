import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FromTextBox";
import validationFields from "../../../utils/validation/validationFields";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import { requiredText } from "../../../utils/validation/rules.js";

const fieldValidations = [
    ruleRunner(validationFields.password, requiredText),
    ruleRunner(validationFields.confirmPassword, requiredText)
];

class ConfirmPasswordResetForm extends Component {
    constructor(props) {
        super(props);

        this.state = {
            password: "",
            confirmPassword: "",
            token: this.props.token,
            submitted: false,
            loading: false,
            error: ""
        };
    };

    validateForm() {
        return (
            this.state.password.length > 0 &&
            this.state.confirmPassword.length > 0 &&
            this.state.password === this.state.confirmPassword
        );
    }

    handleChange = field => {
        return event => {
            this.setState(
                {
                    [field.name]: event.target.value
                },
                function () {
                    let errorsForm = run(this.state, fieldValidations);
                    this.setState({ errors: { $set: errorsForm } });
                }
            );
        };
    };

    handleSubmit = event => {
        event.preventDefault();
        this.setState({ submitted: true });
        this.setState({ loading: true });

        userService.confirmPasswordReset(this.state.password, this.state.token).then(response => {
            console.log("Response from user service: ", response);
            if (response.status === 201) {
                const { from } = { from: { pathname: "/login" } };
                this.props.history.push(from);
            } else {
                this.setState({
                    error: response.messsage,
                    loading: false
                });
            }
        });
    };

    render() {
        const { password, confirmPassword, token, submitted, loading, error } = this.state;

        return (
            <div className="ResetPassword">
                {error && <div className={"alert alert-danger"}>{error}</div>}
                <form onSubmit={this.handleSubmit}>
                    <p className="h5 text-center mb-4">Reset password</p>
                    <div class="col">
                        <div>
                            <FormTextBox
                                id={validationFields.password.name}
                                type="password"
                                placeholder={validationFields.password.display}
                                onChange={this.handleChange(validationFields.password)}
                                value={password}
                                label={validationFields.password.display}
                            />
                        </div>
                        <div>
                            <FormTextBox
                                id={validationFields.confirmPassword.name}
                                type="password"
                                placeholder={validationFields.confirmPassword.display}
                                onChange={this.handleChange(validationFields.confirmPassword)}
                                value={confirmPassword}
                                label={validationFields.confirmPassword.display}
                            />
                        </div>
                        <div>
                            <button
                                type="submit"
                                class="btn btn-primary"
                                disabled={!this.validateForm() || loading}
                            >
                                Submit
                            </button>
                        </div>
                        {loading && (
                            <img src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA==" />
                        )}
                    </div>
                </form>

            </div>
        );
    };
}

export default withRouter(ConfirmPasswordResetForm);

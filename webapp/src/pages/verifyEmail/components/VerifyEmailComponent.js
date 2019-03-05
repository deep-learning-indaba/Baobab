import React, { Component } from "react";
import { userService } from "../../../services/user";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";

class VerifyEmailComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      loading: false,
      error: ""
    };
  }

  componentDidMount() {
    if (this.props.location && this.props.location.search) {
        this.setState({
            verifyToken: this.props.location.search.substring(this.props.location.search.indexOf('=') + 1),
            loading: true
        }, ()=> {
            userService.verifyEmail(this.state.verifyToken).then(response=> {
                this.setState({
                    error: response.error,
                    loading: false
                }, () => {
                    // Redirect to login after short delay to allow user to see that their email was verified.
                    setTimeout(()=>{
                        this.props.history.push("/login");
                    }, 3000);
                });
            })
        });
    } 
    else {
        this.setState({
            error: "No verification token provided."
        });
    }
  }

  render() {
      const {error, loading} = this.state;
      if (loading) {
          return <img src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA==" />
      }

      if (error) {
        return <div class="alert alert-danger">{error}</div>
      }
      
      return (
        <div className={"verify-email"}>
          <p className="h5 text-center mb-4">Verify Email Address</p>
          <div class="col">
            Your email address has been verified. <Link to="/login">Click here</Link> to login if you are not automatically redirected.
          </div>
        </div>
      )
  }

}

export default withRouter(VerifyEmailComponent);
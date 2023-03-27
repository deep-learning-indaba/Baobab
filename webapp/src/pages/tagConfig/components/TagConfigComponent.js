import React, { Component } from "react";
import { tagsService } from "../../../services/tags";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";

class TagConfigComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      tags: [],
      isMultiLingual: this.props.organisation.languages.length > 1,
      isValid: false,
      loading: false,
      error: "",
      errors: [],
      showErrors: false
    };

    console.log(this.state);
  }

  componentDidMount() {
    if (this.props.event) {
      tagsService.getTagList(this.props.event.id).then(result => {
        this.setState({
          loading: false,
          tags: result.tags,
          error: result.error
        });
      });
    }
  }

  onClickAdd = () => {
    const errors = []; //TDDO, validate tag
    if (errors.length === 0) {
      const tag = null; //TODO
      tagsService.addTag(tag).then(result => {
        if (result.error) {
          this.setState({
            errors: [this.props.t(result.error)],
            showErrors: true
          });
        }
        else {
          //this.props.history.goBack();
        }});
    }
    else {
      this.setState({
        showErrors: true
      });
    }
  };

  onClickUpdate = () => {
    const errors = []; //TODO, validate tag
    if (errors.length === 0) {
      const tag = null; //TODO
      tagsService.updateTag(tag).then(result => {
        if (result.error) {
          this.setState({
            errors: [this.props.t(result.error)],
            showErrors: true
          });
        }
        else {
          //go back to tag table
        }});
    }
    else {
      this.setState({
        showErrors: true
      });
    }
  };

  onClickDelete = () => {
    const tag = null; //TODO
    tagsService.deleteTag(tag).then(result => { //TODO: will fail, need to add deleteTag to tagsService
      if (result.error) {
        this.setState({
          errors: [this.props.t(result.error)],
          showErrors: true
        });
      }
      else {
        //go back to tag table
      }});
  }

  getErrorMessages = errors => {
    const errorMessages = [];

    for (let i = 0; i < errors.length; i++) {
      errorMessages.push(
        <div key={"error_"+i} className={"alert alert-danger alert-container"}>
          {errors[i]}
        </div>
      );
    }
    return errorMessages;
  };

  validateTag = (tag) => {
    let errors = [];
    if (tag.name.length === 0) {
      errors.push(this.props.t("Tag name is required"));
    }
    if (tag.type.length === 0) {
      errors.push(this.props.t("Tag type is required"));
    }
    return errors;
  };

  updateTextField = (fieldName, e, lang) => {
    //TODO
  };

  updateDropDown = (fieldName, dropdown) => {
    //TODO
  };

  updateState = (tags) => {
    //TODO
  }

  renderTagTable = () => {
    const tagRows = [];
    //TODO
    return <div></div>;
  }

  render() {
    const {
      loading,
      error,
    } = this.state;

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    if (loading) {
      return (
        <div className="d-flex justify-content-center">
          <div className="spinner-border"
            style={loadingStyle}
            role="status">
            <span className="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    if (error) {
      return <div className="alert alert-danger alert-container">
        {error}
      </div>;
    }

    const t = this.props.t;

    return (
      <div>
        <div className="card">
          <form>
          {this.renderTagTable()}
          {this.state.showErrors && this.getErrorMessages(this.state.errors)}
          </form>
        </div>
      </div>)        
  }
}

export default withRouter(withTranslation()(TagConfigComponent));

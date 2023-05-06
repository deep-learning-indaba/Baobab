import React, { Component } from "react";
import { tagsService } from "../../../services/tags";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';
import FormTextBox from "../../../components/form/FormTextBox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormSelect from "../../../components/form/FormSelect";
import ReactTable from 'react-table';
import { ConfirmModal } from "react-bootstrap4-modal";

//TODO not auto loading when tag is added or edited
//TODO test multilingual language

class TagConfigComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      tags: [],
      updatedTag: {
        name: {},
        tag_type: "",
        description: {},
        active: true
      },
      tag_types: [],
      isMultiLingual: this.props.organisation.languages.length > 1,
      isValid: false,
      loading: false,
      error: "",
      errors: [],
      showErrors: false,
      tagEntryVisible: false,
      confirmRemoveTagVisible: false
    };
  }

  componentDidMount() {
    if (this.props.event) {
      Promise.all([
        tagsService.getTagListConfig(this.props.event.id),
        tagsService.getTagTypeList(this.props.event.id),
        ]).then(([tagsResponse, tagTypesResponse]) => {
          this.setState({
              tags: tagsResponse.tags,
              tag_types: tagTypesResponse.tag_types,
              error: tagsResponse.error || tagTypesResponse.error,
              loading: false,
          });
        });
    }
  }

  addNewTag = () => {
    const errors = this.validateTagDetails();
    if (errors.length === 0) {
      tagsService.addTag(this.state.updatedTag, this.props.event.id).then(result => {
        if (result.status === 201) {
          this.setState({
            updatedTag: {
              name: {},
              tag_type: "",
              description: {},
              active: true
            },
            tagEntryVisible: false,
            confirmRemoveTagVisible: false
          });
        }
        else if (result.error) {
          this.setState({
            errors: [this.props.t(result.error)],
            showErrors: true,
            confirmRemoveTagVisible: false
          });
        }
      });
    }
    else {
      this.setState({
        showErrors: true,
        errors: errors,
        confirmRemoveTagVisible: false
      });
    }
  };

  updateExistingTag = () => {
    const errors = this.validateTagDetails();
    if (errors.length === 0) {
      tagsService.updateTag(this.state.updatedTag, this.props.event.id).then(result => {
        if (result.status === 200) {
          this.setState({
            updatedTag: {
              name: {},
              tag_type: "",
              description: {},
              active: true
            },
            tagEntryVisible: false,
            confirmRemoveTagVisible: false
          });
        }
        else if (result.error) {
          this.setState({
            errors: [this.props.t(result.error)],
            showErrors: true,
            confirmRemoveTagVisible: false
          });
        }
      });
    }
    else {
      this.setState({
        showErrors: true,
        errors: [this.props.t(errors)],
        confirmRemoveTagVisible: false
      });
    }
  };

  onClickEdit = (tag) => {
    this.setState({
      updatedTag: tag
    }, () => {
      this.setTagEntryVisible()
    });
  }

  onClickDelete = (tag) => {
    tag.active = false;
    this.setState({
      updatedTag : tag,
      confirmRemoveTagVisible: true
    }, () => {
      this.updateExistingTag();
    });
  }

  onClickSave = () => {
    if (this.state.updatedTag.id) {
      this.updateExistingTag();
    }
    else {
      this.addNewTag();
    }
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

  validateTagDetails = () => {
    let errors = [];
    this.props.organisation.languages.forEach(lang => {
      if (!this.state.updatedTag.name || !this.state.updatedTag.name[lang.code] || this.state.updatedTag.name[lang.code].trim().length === 0) {
        const error_text = (this.state.isMultiLingual ? this.getFieldNameWithLanguage("Tag name", lang.description) : "Tag name") + " is required"
        errors.push(this.props.t(error_text));
      }
      if (!this.state.updatedTag.description || !this.state.updatedTag.description[lang.code] || this.state.updatedTag.description[lang.code].trim().length === 0) {
        const error_text = (this.state.isMultiLingual ? this.getFieldNameWithLanguage("Tag description", lang.description) : "Tag description") + " is required"
        errors.push(this.props.t(error_text));
      }
    });
    if (!this.state.updatedTag.tag_type || this.state.updatedTag.tag_type.trim().length === 0) {
      errors.push(this.props.t("Tag type is required"));
    }
    return errors;
  };

  updateTextField = (fieldName, e, lang) => {
    let u;
    if (lang) {
      u = {
        ...this.state.updatedTag,
        [fieldName]: {
          ...this.state.updatedTag[fieldName],
          [lang]: e.target.value
        }
      };
    }
    else {
      u = {
        ...this.state.updatedTag,
        [fieldName]: e.target.value
      };
    }
    this.updateState(u);
  };

  updateDropDown = (fieldName, dropdown) => {
    const u = {
      ...this.state.updatedTag,
      [fieldName]: dropdown.value
    };
    this.updateState(u);
  };

  updateState = (tag) => {
    this.setState({
      updatedTag: tag
    }, () => {

      const errors = this.validateTagDetails();

      this.setState({
        errors: errors,
        isValid: errors.length === 0
      });
    });
  }

  renderTagEntry = () => {
    const t = this.props.t;
    return <div className={"form-group margin-top-20px"} key="tag-entry-form">
      <div className={"form-group row"}>
        <label
          className={"col-sm-2 col-form-label"}
          htmlFor={"tag_type"}>
          <span className="required-indicator">*</span>
          {t("Tag Type")}
        </label>
        <div className="col-sm-10">
          <FormSelect
            id={"tag_type"}
            name={"tag_type"}
            required={true}
            defaultValue={this.state.updatedTag.tag_type || null}
            onChange={this.updateDropDown}
            options={
              this.state.tag_types.map((tagType) => ({
                value: tagType,
                label: t(tagType)
              }))
            }
          />
        </div>
      </div>

      {this.props.organisation.languages.map((lang) => (
        <div className={"form-group row"} key={"name_div"+lang.code}>
          <label
            className={"col-sm-2 col-form-label"}
            htmlFor={"name_" + lang.code}>
            <span className="required-indicator">*</span>
            {this.state.isMultiLingual ? t(this.getFieldNameWithLanguage("Tag Name", lang.description)) : t("Tag Name")}
          </label>

          <div className="col-sm-10">
              <FormTextBox
              id={"name_" + lang.code}
              name={"name_" + lang.code}
              type="text"
              placeholder={this.state.isMultiLingual ? t(this.getFieldNameWithLanguage("Name of the tag", lang.description)) : t("Name of the tag")}
              required={true}
              onChange={e => this.updateTextField("name", e, lang.code)}
              value={this.state.updatedTag.name[lang.code] || ""}
              />
          </div>
        </div>
      ))}
      {this.props.organisation.languages.map((lang) => (
        <div className={"form-group row"} key={"description_div"+lang.code}>
          <label
            className={"col-sm-2 col-form-label"}
            htmlFor={"description_" + lang.code}>
            <span className="required-indicator">*</span>
            {this.state.isMultiLingual ? t(this.getFieldNameWithLanguage("Tag Description", lang.description)) : t("Tag Description")}
          </label>
            
          <div className="col-sm-10">
              <FormTextArea
              id={"description_" + lang.code}
              name={"description_" + lang.code}
              type="text"
              placeholder={this.state.isMultiLingual ? t(this.getFieldNameWithLanguage("Description of the tag", lang.description)) : t("Description of the tag")}
              required={true}
              onChange={e => this.updateTextField("description", e, lang.code)}
              value={this.state.updatedTag.description[lang.code] || ""}
              />
          </div>

          {this.state.updatedTag.tag_type && this.state.updatedTag.tag_type === "GRANT" &&
            <div className="required-indicator ml-2">{t("Note, the grant name and description will be visible to users when asked to accept/reject the grant.")}
            </div>}
        </div>
      ))}
      
      <div className={"form-group row"} key="save-tag">
        <div className="col-sm-2 ml-md-auto pr-2 pl-2">
          <button
            onClick={() => this.setState({ tagEntryVisible: false })}
            className="btn btn-danger btn-block">
            {t("Cancel")}
          </button>
        </div>
        <div className="col-sm-2 pr-2 pl-2">
          <button
            onClick={() => this.onClickSave()}
            className="btn btn-primary btn-block">
            {t("Save Tag")}
            </button>
        </div>
      </div>
    </div>;
  }

  setTagEntryVisible = () => {
    this.setState({
      tagEntryVisible: true
      });
  }

  getFieldNameWithLanguage = (input, lang) => {
    return input + " in " + lang;
  }

  render() {
    const {
      loading,
      error,
      tagEntryVisible
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
    const current_lang = this.props.i18n.language;

    const columns = [{
      id: "tag_name",
      Header: <div className="tag-name">{t("Tag Name")}</div>,
      accessor: u => u.name[current_lang],
      minWidth: 150
  }, {
      id: "tag_description",
      Header: <div className="tag-description">{t("Tag Description")}</div>,
      accessor: u => u.description[current_lang],
      minWidth: 150
  }, {
      id: "tag_type",
      Header: <div className="tag-type">{t("Tag Type")}</div>,
      accessor: u => u.tag_type,
      minWidth: 80
  }, {
      id: "actions",
      Header: <div className="actions"/>,
      Cell: props => <div className="action-buttons">
        <i className="fa fa-edit" onClick={() => this.onClickEdit(props.original)}></i>
        <i className="fa fa-trash" onClick={() => this.onClickDelete(props.original)}></i>
      </div>,
      minWidth: 50
    }
  ];

    return (
      <div key='card-container'>
        <div className="card" key="tag-table">
          <div className="react-table">
              <ReactTable
                className="ReactTable"
                data={this.state.tags}
                columns={columns}
                minRows={0}
              />
            </div>
          {!tagEntryVisible && 
            <div className={"row-mb-3"}>
              <button
                onClick={() => this.setTagEntryVisible()}
                className="btn btn-primary float-right margin-top-10px">
                {t("New Tag")}
              </button>
            </div>
          }
          {tagEntryVisible && this.renderTagEntry()}
          {this.state.showErrors && this.getErrorMessages(this.state.errors)}
        </div>

        <ConfirmModal
          visible={this.state.confirmRemoveTagVisible}
          onOK={this.updateExistingTag}
          onCancel={() => this.setState({ confirmRemoveTagVisible: false })}
          okText={t("Yes")}
          cancelText={t("No")}>
          <p>
            {t('Are you sure you want to delete this tag? This will also un-tag all entities with this tag.')}
          </p>
        </ConfirmModal>
      </div>)        
  }
}

export default withRouter(withTranslation()(TagConfigComponent));

import React, { Component } from "react";
import { tagsService } from "../../../services/tags";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';
import FormTextBox from "../../../components/form/FormTextBox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormSelect from "../../../components/form/FormSelect";
import ReactTable from 'react-table';
import { ConfirmModal } from "../../../components/Modal";

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
            confirmRemoveTagVisible: false,
            tags: [...this.state.tags, result.tag]
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
            confirmRemoveTagVisible: false,
            tags: result.tag.active ? this.state.tags.map(tag => {
                  return tag.id === result.tag.id ? result.tag : tag;
                })
                : this.state.tags.filter(tag => {
                  return tag.id !== result.tag.id;
                })
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
    return (
      <div className="space-y-6 p-6 bg-slate-50/50 rounded-xl border border-border mt-6 text-left" key="tag-entry-form">
        <h3 className="text-lg font-semibold text-foreground/90 pb-2 border-b border-border/50">{t("Tag Details")}</h3>
        
        <div className="space-y-2">
          <label
            className="block text-sm font-semibold text-foreground/90"
            htmlFor="tag_type">
            <span className="text-error mr-1">*</span>
            {t("Tag Type")}
          </label>
          <FormSelect
            id="tag_type"
            name="tag_type"
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

        {this.props.organisation.languages.map((lang) => (
          <div className="space-y-2" key={"name_div"+lang.code}>
            <label
              className="block text-sm font-semibold text-foreground/90"
              htmlFor={"name_" + lang.code}>
              <span className="text-error mr-1">*</span>
              {this.state.isMultiLingual ? t(this.getFieldNameWithLanguage("Tag Name", lang.description)) : t("Tag Name")}
            </label>
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
        ))}

        {this.props.organisation.languages.map((lang) => (
          <div className="space-y-2" key={"description_div"+lang.code}>
            <label
              className="block text-sm font-semibold text-foreground/90"
              htmlFor={"description_" + lang.code}>
              <span className="text-error mr-1">*</span>
              {this.state.isMultiLingual ? t(this.getFieldNameWithLanguage("Tag Description", lang.description)) : t("Tag Description")}
            </label>
            <FormTextArea
              id={"description_" + lang.code}
              name={"description_" + lang.code}
              placeholder={this.state.isMultiLingual ? t(this.getFieldNameWithLanguage("Description of the tag", lang.description)) : t("Description of the tag")}
              required={true}
              rows={3}
              onChange={e => this.updateTextField("description", e, lang.code)}
              value={this.state.updatedTag.description[lang.code] || ""}
            />
            {this.state.updatedTag.tag_type && this.state.updatedTag.tag_type === "GRANT" && (
              <p className="text-xs text-muted-foreground mt-1">
                {t("Note, the grant name and description will be visible to users when asked to accept/reject the grant.")}
              </p>
            )}
          </div>
        ))}

        <div className="flex flex-col md:flex-row items-center justify-end gap-4 pt-4 border-t border-border/50" key="save-tag">
          <button
            onClick={() => this.setState({ tagEntryVisible: false })}
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-error text-error-foreground hover:bg-error/90 shadow-sm w-full md:w-auto">
            {t("Cancel")}
          </button>
          <button
            onClick={() => this.onClickSave()}
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm w-full md:w-auto">
            {t("Save Tag")}
          </button>
        </div>
      </div>
    );
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

    if (loading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
          {error}
        </div>
      );
    }

    const t = this.props.t;
    const current_lang = this.props.i18n.language;

    const columns = [{
      id: "tag_name",
      Header: <div className="tag-name text-left font-bold">{t("Tag Name")}</div>,
      accessor: u => u.name[current_lang],
      minWidth: 150
  }, {
      id: "tag_description",
      Header: <div className="tag-description text-left font-bold">{t("Tag Description")}</div>,
      accessor: u => u.description[current_lang],
      minWidth: 150
  }, {
      id: "tag_type",
      Header: <div className="tag-type text-left font-bold">{t("Tag Type")}</div>,
      accessor: u => u.tag_type,
      minWidth: 80
  }, {
      id: "actions",
      Header: <div className="actions"/>,
      Cell: props => <div className="action-buttons flex gap-2">
        <i className="fa fa-edit cursor-pointer hover:text-primary transition-colors text-lg" onClick={() => this.onClickEdit(props.original)}></i>
        <i className="fa fa-trash cursor-pointer hover:text-error transition-colors text-lg" onClick={() => this.onClickDelete(props.original)}></i>
      </div>,
      minWidth: 50
    }
  ];

    return (
      <div key='card-container' className="w-full max-w-5xl mx-auto pt-6 text-left">
        <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6" key="tag-table">
          <h1 className="font-heading text-2xl font-bold text-foreground mb-6">{t("Tags")}</h1>
          <div className="react-table">
              <ReactTable
                className="ReactTable"
                data={this.state.tags}
                columns={columns}
                minRows={0}
              />
            </div>
          {!tagEntryVisible && 
            <div className="flex justify-end pt-4">
              <button
                onClick={() => this.setTagEntryVisible()}
                className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm">
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

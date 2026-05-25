import React, { Component } from "react";
import { withRouter } from "react-router";
import { invitedGuestServices } from "../../../services/invitedGuests/invitedGuests.service";
import { tagsService } from "../../../services/tags/tags.service";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import "react-table/react-table.css";
import validationFields from "../../../utils/validation/validationFields";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import ReactTable from 'react-table';
import { Trans, withTranslation } from 'react-i18next';
import TagSelectorDialog from '../../../components/TagSelectorDialog';
import { downloadCSV } from "../../../utils/files";
import {
  requiredText,
  requiredDropdown,
  validEmail
} from "../../../utils/validation/rules.js";
import {
  getTitleOptions
} from "../../../utils/validation/contentHelpers";
import { ConfirmModal } from "../../../components/Modal";

const baseFieldValidations = [
  ruleRunner(validationFields.email, validEmail),
  ruleRunner(validationFields.role, requiredDropdown)
];

const extraFieldValidations = [
  ruleRunner(validationFields.title, requiredDropdown),
  ruleRunner(validationFields.firstName, requiredText),
  ruleRunner(validationFields.lastName, requiredText),
]

class InvitedGuests extends Component {
  constructor(props) {
    super(props);
    this.assignable_tag_types = ["REGISTRATION", "GRANT"];
    this.state = {
      isLoading: true,
      isError: false,
      guestList: [],
      user: {
        tag_ids: []
      },
      addedSucess: false,
      notFound: false,
      buttonClicked: false,
      conflict: false,
      error: "",
      errors: {},
      successMessage: "",
      adding: false,
      roleSearch: "all",
      nameSearch: "",
      tagSearch: '',
      tags: [],
      filteredTags: [],
      tagSelectorVisible: false,
      selectedGuest: null,
      confirmRemoveGuestVisible: false,
      newGuestTags: []
    };
  }

  getGuestList() {
    const eventId = this.props.event ? this.props.event.id : 0;

    Promise.all([
      invitedGuestServices.getInvitedGuestList(eventId),
      tagsService.getTagList(eventId)
    ]).then(([guestResponse, tagsResponse]) => {
      this.setState({
        loading: false,
        guestList: guestResponse.guests,
        filteredList: guestResponse.guests,
        tags: tagsResponse.tags,
        error: guestResponse.error || tagsResponse.error
      });
    });
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList;
    } else
      return [];
  }

  componentDidMount() {
    this.setState({ loading: true }, () => this.getGuestList());
    getTitleOptions.then(result => {
      this.setState({
        titleOptions: this.checkOptionsList(result)
      });
    });
  }

  runValidations = callback => {
    let fieldValidations = baseFieldValidations;
    if (this.state.notFound) {
      fieldValidations = fieldValidations.concat(extraFieldValidations);
    }
    let errorsForm = run(this.state.user, fieldValidations);
    if (!callback) {
      callback = () => { }
    }
    this.setState({ errors: { $set: errorsForm } }, callback);
  }

  handleChangeDropdown = (name, dropdown) => {
    this.setState(
      {
        user: {
          ...this.state.user,
          [name]: dropdown.value
        }
      },
      this.runValidations
    );
  };

  handleChange = field => {
    return event => {
      this.setState({
        user: {
          ...this.state.user,
          [field.name]: event.target.value
        }
      },
        this.runValidations
      );
    };
  };

  convertToCsv = (guestList) => {
    var str = "NAME,EMAIL,ROLE,TAGS\r\n";

    for (var i = 0; i < guestList.length; i++) {
      const tags = guestList[i].tags.map(t=>t.name).join("; ");
      const fullname = guestList[i].user.user_title + " " + guestList[i].user.firstname + " " + guestList[i].user.lastname
      str += fullname + ',' + guestList[i].user.email + ',' + guestList[i].role + ',' + tags;
      str += "\r\n";
    }
    return str;
  };

  downloadCsv = () => {
    let csv = this.convertToCsv(this.state.guestList);
    var filename = "GuestList" + new Date().toDateString().split(" ").join("_") + ".csv";
    downloadCSV(csv, filename);
  };

  filterGuestList = () => {
    const { nameSearch, roleSearch, tagSearch } = this.state;
    const filtered = this.state.guestList.filter(g => {
      let passed = true;
      if (nameSearch) {
        const fullname = g.user.user_title + " " + g.user.firstname + " " + g.user.lastname;
        passed = (fullname.toLowerCase().indexOf(nameSearch.toLowerCase()) > -1
          || g.user.email.toLowerCase().indexOf(nameSearch.toLowerCase()) > -1);
      }
      if (roleSearch && passed && roleSearch !== "all") {
        passed = g.role === roleSearch;
      }
      if (tagSearch && passed && tagSearch !== "all") {
        passed = g.tags.some(tag => tag.id.toString() === tagSearch);
      }
      return passed;
    });
    this.setState({ filteredList: filtered });
  }

  updateNameSearch = (event) => {
    this.setState({nameSearch: event.target.value}, this.filterGuestList);
  }

  updateRoleSearch = (id, event) => {
    this.setState({roleSearch: event.value}, this.filterGuestList);
  }

  updateTagSearch = (id, event) => {
    const newTagSearch = event.value;
    if (newTagSearch === 'all') {
      this.setState({ tagSearch: '' }, this.filterGuestList);
      return;
    }
    this.setState({ tagSearch: event.value }, this.filterGuestList);
  };

  getSearchRoles(roles) {
    return [{ value: "all", label: this.props.t("All") }, ...roles];
  }

  handleResponse = response => {
    if (response.msg === "succeeded") {
      this.setState({
        addedSucess: true,
        conflict: false,
        notFound: false,
        successMessage: this.props.t("Added") + " " + response.response.data.fullname + " " + this.props.t("to the guest list"),
        user: {
          tag_ids: []
        },
        newGuestTags: [],
        showErrors: false,
        adding: false
      }, this.getGuestList);
    } else if (response.msg === "404") {
      this.setState({
        addedSucess: false,
        notFound: true,
        conflict: false,
        successMessage: "",
        adding: false
      }, this.getGuestList);
    } else if (response.msg === "409") {
      this.setState({
        notFound: false,
        addedSucess: false,
        conflict: true,
        user: {},
        successMessage: "",
        showErrors: false,
        adding: false
      }, this.getGuestList);
    } else {
      this.setState({
        error: response.error,
        adding: false
      });
    }
  }

  buttonSubmit() {
    this.runValidations(() => {
      let errors = this.state.errors;
      if (errors && errors.$set && errors.$set.length > 0) {
        this.setState({ showErrors: true });
        return;
      }

      const user = {
        ...this.state.user,
        tag_ids: this.state.newGuestTags.map(tag => tag.id)
      };

      this.setState({ adding: true });
      invitedGuestServices
        .addInvitedGuest(user.email,
          this.props.event ? this.props.event.id : 0,
          user.role,
          user.tag_ids)
        .then(resp => this.handleResponse(resp));
    });
  }

  submitCreate = () => {
    this.runValidations(() => {
      let errors = this.state.errors;
      if (errors && errors.$set && errors.$set.length > 0) {
        this.setState({ showErrors: true });
        return;
      }
      const user = {
        ...this.state.user,
        tag_ids: this.state.newGuestTags.map(tag => tag.id)
      };

      this.setState({ adding: true });

      invitedGuestServices
        .createInvitedGuest(user, this.props.event ? this.props.event.id : 0, user.role)
        .then(resp => this.handleResponse(resp));
    });
  }

  getError = id => {
    if (!this.state.showErrors) {
      return "";
    }

    if (this.state.errors &&
      this.state.errors.$set &&
      this.state.errors.$set.length > 0) {

      let errorMessage = this.state.errors.$set.find(e => e[id]);

      if (errorMessage) {
        return Object.values(errorMessage)[0];
      }
      return "";
    }
    return "";
  }

  addTag = (guest) => {
    const tagIds = guest.tags.map(t=>t.id);
    this.setState({
      selectedGuest: guest,
      tagSelectorVisible: true,
      filteredTags: this.state.tags.filter(t=>!tagIds.includes(t.id) && this.assignable_tag_types.includes(t.tag_type))
    })
  }

  onSelectTag = (tag) => {
    invitedGuestServices.addTag(this.state.selectedGuest.invited_guest_id, this.props.event.id, tag.id)
    .then(resp => {
      if (resp.statusCode === 201) {
        const newGuest = {
          ...this.state.selectedGuest,
          tags: [...this.state.selectedGuest.tags, resp.response.data]
        }
        const newGuests = this.state.guestList.map(g => 
            g.invited_guest_id === this.state.selectedGuest.invited_guest_id  ? newGuest : g);
        this.setState({
          tagSelectorVisible: false,
          selectedGuest: null,
          filteredTags: [],
          guestList: newGuests
        }, this.filterGuestList);
      }
      else {
        this.setState({
          tagSelectorVisible: false,
          selectedGuest: null,
          error: resp.error
        });
      }
    })
  }

  confirmRemoveTag = () => {
    const {selectedGuest, selectedTag} = this.state;

    invitedGuestServices.removeTag(selectedGuest.invited_guest_id, this.props.event.id, selectedTag.id)
    .then(resp => {
      if (resp.statusCode === 200) {
        const newGuest = {
          ...selectedGuest,
          tags: selectedGuest.tags.filter(t=>t.id !== selectedTag.id)
        }
        const newGuests = this.state.guestList.map(g => 
            g.invited_guest_id === selectedGuest.invited_guest_id  ? newGuest : g);
        this.setState({
          guestList: newGuests,
          confirmRemoveTagVisible: false
        }, this.filterGuestList);
      }
      else {
        this.setState({
          error: resp.error,
          confirmRemoveTagVisible: false
        });
      }
    })

  }

  removeTag = (guest, tag) => {
    this.setState({
      selectedGuest: guest,
      selectedTag: tag,
      confirmRemoveTagVisible: true
    });
  }

  handleDeleteGuest = (resp) => {
    if (resp.statusCode === 200) {
      const removedGuest = this.state.guestList.find(g => g.invited_guest_id === resp.response.data.invited_guest_id);
      const guestName = removedGuest.user.user_title + " " + removedGuest.user.firstname + " " + removedGuest.user.lastname;
      this.setState({
        guestList: this.state.guestList.filter(g => g.invited_guest_id !== resp.response.data.invited_guest_id),
        addedSucess: true,
        selectedGuest: null,  // Reset selectedGuest to prevent issues when adding new guests
        successMessage: <Trans i18nKey="removed_guest" values={{ guestName }}>Removed {{guestName}} from the guest list</Trans>
      }, this.filterGuestList);
    }
    else {
      this.setState({
        error: resp.error,
        selectedGuest: null  // Also reset on error to be safe
      });
    }
  }

  removeGuest = (guest) => {
    this.setState({
      selectedGuest: guest,
      confirmRemoveGuestVisible: true
    });
  }

  confirmRemoveGuest = () => {
    const guest = this.state.selectedGuest;
    invitedGuestServices.deleteGuest(guest.invited_guest_id, this.props.event.id)
      .then(resp => {
        this.setState({
          confirmRemoveGuestVisible: false
        }, () => this.handleDeleteGuest(resp));
      });
  }

  render() {
    const t = this.props.t;
    const { loading, error } = this.state;
    const roleOptions = invitedGuestServices.getRoles()
    const searchRoleOptions = this.getSearchRoles(roleOptions);

    if (loading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    const columns = [{
      id: "user",
      Header: <div className="invitedguest-fullname text-left font-bold">{t("Full Name")}</div>,
      accessor: u =>
        <div className="invitedguest-fullname font-medium text-foreground">
          {u.user.user_title + " " + u.user.firstname + " " + u.user.lastname}
        </div>,
      minWidth: 150
    }, {
      id: "email",
      Header: <div className="invitedguest-email text-left font-bold">{t("Email")}</div>,
      accessor: u => u.user.email
    }, {
      id: "role",
      Header: <div className="invitedguest-role text-left font-bold">{t("Role")}</div>,
      accessor: u => u.role
    }, {
      id: "tags",
      Header: <div className="invitedguest-tags text-left font-bold">{t("Tags")}</div>,
      Cell: props => <div className="flex flex-wrap gap-1 items-center">
        {props.original.tags.map(t => 
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 cursor-pointer select-none" onClick={()=>this.removeTag(props.original, t)} key={`tag_${props.original.invited_guest_id}_${t.id}`}>{t.name}</span>)}
        <i className="fa fa-plus-circle text-primary hover:text-primary/80 transition-colors text-base cursor-pointer ml-1" onClick={() => this.addTag(props.original)}></i>
      </div>,
      accessor: u => u.tags.map(t => t.name).join("; ")
    },
    {
      id: "remove",
      Header: <div className="invitedguest-remove text-left font-bold">{t("Remove")}</div>,
      accessor: u => (
        <button 
          className="inline-flex items-center justify-center p-2 rounded-lg text-sm font-semibold transition-colors bg-error/10 text-error hover:bg-error/20 border border-error/20 cursor-pointer"
          onClick={() => this.removeGuest(u)}
        >
          <i className="fa fa-trash"></i>
        </button>
      )
    }
  ];

  const guestName = this.state.selectedGuest ? this.state.selectedGuest.user.user_title + " " + this.state.selectedGuest.user.firstname + " " + this.state.selectedGuest.user.lastname : "";

    return (
      <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
        {error && (
          <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
            {JSON.stringify(error)}
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6" key="tag-table">
          <h1 className="font-heading text-2xl font-bold text-foreground mb-6">{t("Invited Guests")}</h1>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <FormTextBox
                id="s"
                type="text"
                placeholder="Search"
                onChange={this.updateNameSearch}
                label={t("Filter by name or email")}
                name=""
                value={this.state.nameSearch} />
            </div>

            <div className="space-y-2">
              <FormSelect
                options={searchRoleOptions}
                id="RoleFilter"
                placeholder="search"
                onChange={this.updateRoleSearch}
                label={t("Filter by role")}
                defaultValue={this.state.roleSearch || "all"} />
            </div>

            <div className="space-y-2">
              <FormSelect
                options={[
                  { value: 'all', label: t('All Tags') },
                  ...this.state.tags.map(tag => ({ 
                    value: tag.id.toString(), 
                    label: tag.name 
                  }))
                ]}
                id="TagFilter"
                placeholder={t('Filter by tag')}
                onChange={this.updateTagSearch}
                label={t('Filter by tag')}
                defaultValue={this.state.tagSearch || 'all'}
              />
            </div>
          </div>

          {this.state.guestList && this.state.guestList.length > 0 && (
            <div className="react-table">
              <ReactTable
                data={this.state.filteredList}
                columns={columns}
                minRows={0}
                className="ReactTable"
              />
            </div>
          )}

          {(!this.state.guestList || this.state.guestList.length === 0) && (
            <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center">
              {t("No invited guests")}
            </div>
          )}

          <div className="flex justify-end pt-4">
            <button
              className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-xs font-semibold transition-colors border border-border text-muted-foreground hover:bg-slate-50 cursor-pointer bg-white"
              onClick={() => this.downloadCsv()}>
              <i className="fas fa-download mr-1.5"></i>
              {t("Download csv")}
            </button>
          </div>
        </div>

        {this.state.addedSucess && (
          <div className="bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl text-sm text-center">
            {this.state.successMessage}
          </div>
        )}

        {this.state.addedSucess === false && this.state.conflict && (
          <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm text-center">
            {t("Invited guest with this email already exists.")}
          </div>
        )}

        <form onSubmit={e => e.preventDefault()}>
          <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
            <h3 className="text-lg font-bold text-foreground/90">{t("Add Guest")}</h3>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
              <div className="space-y-2">
                <FormTextBox
                  id={validationFields.email.name}
                  type="email"
                  placeholder={t(validationFields.email.display)}
                  onChange={this.handleChange(validationFields.email)}
                  label={t(validationFields.email.display)}
                  showError={this.getError(validationFields.email.name)}
                  errorText={this.getError(validationFields.email.name)}
                  value={this.state.user[validationFields.email.name] || ""} />
              </div>

              <div className="space-y-2">
                <FormSelect
                  options={roleOptions}
                  id={validationFields.role.name}
                  placeholder={t(validationFields.role.display)}
                  onChange={this.handleChangeDropdown}
                  label={t(validationFields.role.display)}
                  showError={this.getError(validationFields.role.name)}
                  errorText={this.getError(validationFields.role.name)}
                  defaultValue={this.state.user[validationFields.role.name] || ""}
                  value={this.state.user[validationFields.role.name] || ""} />
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-foreground/90 mb-1">{t("Tags")}</label>
                <div className="flex flex-wrap gap-1 items-center min-h-[46px] border border-border rounded-lg px-4 py-1.5 bg-white">
                  {this.state.newGuestTags.map(tag => (
                    <span key={`new-guest-tag-${tag.id}`} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                      {tag.name}
                      <i 
                        className="fa fa-times ml-1.5 cursor-pointer text-primary hover:text-primary/80 transition-colors" 
                        onClick={() => this.setState({
                          newGuestTags: this.state.newGuestTags.filter(t => t.id !== tag.id)
                        })} 
                      />
                    </span>
                  ))}
                  <i 
                    className="fa fa-plus-circle text-primary hover:text-primary/80 transition-colors text-lg cursor-pointer ml-1" 
                    onClick={() => this.setState({
                      tagSelectorVisible: true,
                      filteredTags: this.state.tags.filter(tag => 
                        !this.state.newGuestTags.some(t => t.id === tag.id) && 
                        this.assignable_tag_types.includes(tag.tag_type)
                      )
                    })}
                  />
                </div>
              </div>

              <div>
                {!this.state.notFound ? (
                  <button
                    type="button"
                    className="w-full inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm cursor-pointer h-[46px]"
                    onClick={() => this.buttonSubmit()}
                    disabled={this.state.adding}>
                    {this.state.adding && (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1.5"></div>
                    )}
                    {t("Add")}
                  </button>
                ) : !this.state.addedSucess && this.state.notFound ? (
                  <span className="text-warning font-semibold text-sm">
                    {t("User does not exist, please add details below")}:
                  </span>
                ) : null}
              </div>
            </div>

            {!this.state.addedSucess && this.state.notFound && (
              <div className="space-y-6 pt-6 border-t border-border/50">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <FormSelect
                      options={this.state.titleOptions}
                      id={validationFields.title.name}
                      placeholder={t(validationFields.title.display)}
                      onChange={this.handleChangeDropdown}
                      label={t(validationFields.title.display)}
                      showError={this.getError(validationFields.title.name)}
                      errorText={this.getError(validationFields.title.name)}
                      defaultValue={this.state.user[validationFields.title.name] || ""}
                      value={this.state.user[validationFields.title.name] || ""} />
                  </div>

                  <div className="space-y-2">
                    <FormTextBox
                      id={validationFields.firstName.name}
                      type="text"
                      placeholder={t(validationFields.firstName.display)}
                      onChange={this.handleChange(validationFields.firstName)}
                      label={t(validationFields.firstName.display)}
                      showError={this.getError(validationFields.firstName.name)}
                      errorText={this.getError(validationFields.firstName.name)}
                      value={this.state.user[validationFields.firstName.name] || ""} />
                  </div>

                  <div className="space-y-2">
                    <FormTextBox
                      id={validationFields.lastName.name}
                      type="text"
                      placeholder={t(validationFields.lastName.display)}
                      onChange={this.handleChange(validationFields.lastName)}
                      label={t(validationFields.lastName.display)}
                      showError={this.getError(validationFields.lastName.name)}
                      errorText={this.getError(validationFields.lastName.name)}
                      value={this.state.user[validationFields.lastName.name] || ""} />
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <button
                    type="button"
                    className="inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm cursor-pointer"
                    onClick={() => this.submitCreate()}
                    disabled={this.state.adding}>
                    {this.state.adding && (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1.5"></div>
                    )}
                    {t("Create Invited Guest")}
                  </button>
                </div>
              </div>
            )}
          </div>
        </form>

        <TagSelectorDialog
          visible={this.state.tagSelectorVisible}
          onClose={() => this.setState({ tagSelectorVisible: false })}
          onSelectTag={(tag) => {
            if (this.state.selectedGuest) {
              this.onSelectTag(tag);
            } else {
              this.setState({
                newGuestTags: [...this.state.newGuestTags, tag],
                tagSelectorVisible: false
              });
            }
          }}
          tags={this.state.filteredTags}
          title={t('Add Tag')}
        />

        <ConfirmModal
            visible={this.state.confirmRemoveTagVisible}
            onOK={this.confirmRemoveTag}
            onCancel={() => this.setState({ confirmRemoveTagVisible: false })}
            okText={t("Yes")}
            cancelText={t("No")}>
            <p>
                {t('Are you sure you want to remove this tag?')}
            </p>
        </ConfirmModal>

        <ConfirmModal
            visible={this.state.confirmRemoveGuestVisible}
            onOK={this.confirmRemoveGuest}
            onCancel={() => this.setState({ confirmRemoveGuestVisible: false })}
            okText={t("Yes")}
            cancelText={t("No")}>
            <p>
              <Trans i18nKey="remove_guest_confirmation" values={{ guestName }}>Are you sure you want to remove {{guestName}} from the guest list?</Trans>
            </p>
        </ConfirmModal>
      </div>
    );
  }
}

export default withRouter(withTranslation()(InvitedGuests));

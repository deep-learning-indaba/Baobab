import React, { Component } from 'react';
import Select from 'react-select';
import makeAnimated from 'react-select/lib/animated';
import '../ResponseList.css';
import { Trans, withTranslation } from 'react-i18next'
import { responsesService } from '../../../services/responses/responses.service';
import ReactTable from 'react-table';
import "react-table/react-table.css";
import { NavLink } from "react-router-dom";
import { tagsService } from '../../../services/tags/tags.service';
import FormTextBox from "../../../components/form/FormTextBox";
import { reviewService } from '../../../services/reviews/review.service';
import { ConfirmModal } from "react-bootstrap4-modal";
import TagSelectorDialog from '../../../components/TagSelectorDialog';
import { createColClassName } from "../../../utils/styling/styling";

class ResponseListComponent extends Component {
    constructor(props) {
        super(props);

        this.assignable_tag_types = ["RESPONSE"];

        this.state = {
            btnUpdate: false,
            includeUnsubmitted: false,
            responses: [],
            filteredResponses: [],
            tags: [],
            filteredTags: [],
            tagSelectorVisible: false,
            confirmRemoveTagVisible: false,
            selectedResponse: null,
            error: null,
            loading: true,
            nameSearch : "",
            tagSearch : [],
            emailSearch: "",
            gettingResponseList: false
        }
    }

    componentDidMount() {
        this.setState({ loading: true }, () => this.getResponseList());

    }

    getResponseList() {
        this.setState({ gettingResponseList: true });
        Promise.all([
            tagsService.getTagList(this.props.event.id),
            responsesService.getResponseList(this.props.event.id, this.state.includeUnsubmitted, []),
        ]).then(([tagsResponse, responsesResponse]) => {
            this.setState({
                tags: tagsResponse.tags,
                responses: responsesResponse.responses,
                filteredResponses : responsesResponse.responses,
                error: tagsResponse.error || responsesResponse.error,
                loading: false,
                gettingResponseList: false
            });
        });
    }

    toggleUnsubmitted = () => {
        this.setState({
            includeUnsubmitted: !this.state.includeUnsubmitted
        }, this.getResponseList);
    }

    handleChange = event => {
        const value = event.target.value;
        this.setState({ 
            newReviewerEmail: value,
            reviewerAssignError: "",
            reviewerAssignSuccess: ""
        });
    };

    assignReviewer = () => {
        reviewService.assignResponsesToReviewer(this.props.event.id, this.state.selectedResponseIds, this.state.newReviewerEmail)
            .then(response => {
                this.setState({
                    reviewerAssignError: response.error,
                    newReviewerEmail: response.error ? this.state.newReviewerEmail : "",
                    numReviewsAssigned: response.error ? 0 : this.state.selectedResponseIds.length,
                    assignedReviewerEmail: response.error ? "" : this.state.newReviewerEmail,
                    reviewerAssignSuccess: !response.error
                });
                if (!response.error) {
                    this.filterResponses();
                }
            });
    }

    removeTag = (response, tag) => {
        this.setState({
          selectedResponse: response,
          selectedTag: tag,
          confirmRemoveTagVisible: true
        });
    }
    
    addTag = (response) => {
        const tagIds = response.tags.map(t=>t.id);
        this.setState({
          selectedResponse: response,
          tagSelectorVisible: true,
          filteredTags: this.state.tags.filter(t=>!tagIds.includes(t.id) && this.assignable_tag_types.includes(t.tag_type))
        })
    }

    onSelectTag = (tag) => {
        responsesService.tagResponse(this.state.selectedResponse.response_id, tag.id, this.props.event.id)
        .then(resp => {
            if (resp.status === 201) {
                const newResponse = {
                ...this.state.selectedResponse,
                tags: [...this.state.selectedResponse.tags, tag]
                } 
                const newResponses = this.state.responses.map(r => 
                    r.response_id === this.state.selectedResponse.response_id  ? newResponse : r);
                this.setState({
                tagSelectorVisible: false,
                selectedResponse: null,
                filteredTags: [],
                responses: newResponses
                }, this.filterResponses);
                }
            else {
                this.setState({
                tagSelectorVisible: false,
                error: resp.error
            });
            }
        })
    }
  
  confirmRemoveTag = () => {
    const {selectedResponse, selectedTag} = this.state;

    responsesService.removeTag(selectedResponse.response_id, selectedTag.id, this.props.event.id)
    .then(resp => {
      if (resp.status === 200) {
        const newResponse = {
          ...selectedResponse,
          tags: selectedResponse.tags.filter(t=>t.id !== selectedTag.id)
        }
        const newResponses = this.state.responses.map(r => 
            r.response_id === selectedResponse.response_id ? newResponse : r);
        this.setState({
          responses: newResponses,
          confirmRemoveTagVisible: false
        }, this.filterResponses);
      }
      else {
        this.setState({
          error: resp.error,
          confirmRemoveTagVisible: false
        });
      }
    })
    }

    updateNameSearch = (event) => {
        this.setState({nameSearch: event.target.value}, this.filterResponses);
    }
    
    updateEmailSearch = (event) => {
        this.setState({emailSearch: event.target.value}, this.filterResponses);
    }

    updateTagSearch = (id, event) => {
      const newTagSearch = this.state.tagSearch;
      if (event.action === "remove-value") {
        newTagSearch.splice(newTagSearch.indexOf(event.removedValue.value), 1);
      }
      else if (event.action === "clear") {
        newTagSearch = [];
      }
      else if (event.action === "select-option") {
        newTagSearch.push(event.option.value);
      }
      this.setState({tagSearch: newTagSearch}, this.filterResponses);
    }

    getSearchTags(tags) {
      return tags ? tags.filter(t=>t).map(t => ({ value: t.name, label: t.name})) : tags;
    }

    filterResponses = () => {
        const { nameSearch, tagSearch, emailSearch } = this.state;
        const filtered = this.state.responses.filter(r => {
          let passed = true;
          if (nameSearch) {
            passed = ((r.firstname && r.firstname.toLowerCase().indexOf(nameSearch.toLowerCase()) > -1) 
                      || (r.lastname && r.lastname.toLowerCase().indexOf(nameSearch.toLowerCase()) > -1));
          }
          if (emailSearch && passed) {
            passed = r.email && r.email.toLowerCase().indexOf(emailSearch.toLowerCase()) > -1;
          }
          if (tagSearch.length > 0 && passed) {
            passed = tagSearch && tagSearch.every(t => r.tags.some(rt => rt.name === t));
          }
          return passed;
        });
        this.setState({ filteredResponses: filtered });
      }

    render() {
        const threeColClassName = createColClassName(12, 4, 4, 4);  //xs, sm, md, lg
        const animatedComponents = makeAnimated();
        const t = this.props.t;

        const {
            error,
            loading,
            numReviewsAssigned,
            assignedReviewerEmail,
            reviewerAssignError,
            newReviewerEmail,
            reviewerAssignSuccess,
            filteredTags,
            filteredResponses
        } = this.state

        if (loading) {
            return (
              <div className="d-flex justify-content-center">
                <div className="spinner-border" role="status">
                  <span className="sr-only">Loading...</span>
                </div>
              </div>
            );
          }

        const columns = [{
            id: "response_link",
            Header: <div className="response-link">{t("ID")}</div>,
            accessor: u => <NavLink
                        to={`/${this.props.event.key}/responsePage/${u.response_id}`}
                        className="table-nav-link">
                        {u.response_id}
                        </NavLink>,
            minWidth: 50
        }, {
            id: "user",
            Header: <div className="response-fullname">{t("Full Name")}</div>,
            accessor: u =>
              <div className="response-fullname">
                {u.user_title + " " + u.firstname + " " + u.lastname}
              </div>,
            minWidth: 150
        }, {
            id: "email",
            Header: <div className="response-email">{t("Email")}</div>,
            accessor: u => u.email,
            minWidth: 150
        }, {
            id: "tags",
            Header: <div className="response-tags">{t("Tags")}</div>,
            Cell: props => <div>
              {props.original.tags.map(t => 
                  <span className="tag badge badge-primary" onClick={()=>this.removeTag(props.original, t)} key={`tag_${props.original.response_id}_${t.id}`}>{t.name}</span>)}
              <i className="fa fa-plus-circle" onClick={() => this.addTag(props.original)}></i>
            </div>,
            accessor: u => u.tags.map(t => t.name).join("; "),
            minWidth: 150
          },
          {
            id: "email",
            Header: <div className="response-language">{t("Language")}</div>,
            accessor: u => u.language,
            minWidth: 80
          },
          {
            id: "start_date",
            Header: <div className="response-start-date">{t("Start Date")}</div>,
            accessor: u => u.start_date,
            minWidth: 150
          },
          {
            id: "is_submitted",
            Header: <div className="response-submitted">{t("Submitted")}</div>,
            accessor: u => u.is_submitted ? "True" : "False",
            minWidth: 80
          },
          {
            id: "is_withdrawn",
            Header: <div className="response-withdrawn">{t("Withdrawn")}</div>,
            accessor: u => u.is_withdrawn ? "True" : "False",
            minWidth: 80
          },
          {
            id: "submitted_date",
            Header: <div className="response-submitted-date">{t("Submitted Date")}</div>,
            accessor: u => u.submitted_date,
            minWidth: 150
          },
          {
            id: "reviewers",
            Header: <div className="response-reviewers">{t("Reviewers")}</div>,
            accessor: u => u.reviewers.filter(r=>r).map(r=>r.reviewer_name).join("; "),
            minWidth: 300
          }
        ];

        return (
            <div className="ResponseList container-fluid pad-top-30-md">

                {error &&
                    <div className={"alert alert-danger alert-container"}>
                    {JSON.stringify(error)}
                    </div>}

                <div className="card no-padding-h">
                    <p className="h4 text-center mb-4">{t("Response List")}</p>

                    <div className="row">
                        <div className={threeColClassName}>
                            <label className="col-form-label" htmlFor="NameFilter">{t("Filter by name")}</label>
                            <FormTextBox
                            id="NameFilter"
                            type="text"
                            placeholder="Search"
                            onChange={this.updateNameSearch}
                            name=""
                            value={this.state.nameSearch} />
                        </div>

                        <div className={threeColClassName}>
                          <label className="col-form-label" htmlFor="EmailFilter">{t("Filter by email")}</label>
                            <FormTextBox
                            id="EmailFilter"
                            type="text"
                            placeholder="Search"
                            onChange={this.updateEmailSearch}
                            defaultValue={this.state.emailSearch} />
                        </div>

                        <div className={threeColClassName}>
                            <label className="col-form-label" htmlFor="TagFilter">{t("Filter by tag")}</label>
                            <Select
                              closeMenuOnSelect={false}
                              components={animatedComponents}
                              isMulti
                              options={this.getSearchTags(filteredTags)}
                              id="TagFilter"
                              placeholder="Search"
                              onChange={this.updateTagSearch}
                              defaultValue={"none"}/>
                        </div>
                    </div>
                    
                    <div className="checkbox-top">
                        <input 
                            onClick={(e) => this.toggleUnsubmitted()}
                            className="form-check-input input"
                            type="checkbox"
                            value=""
                            id="toggle_unsubmitted"
                            disabled={this.state.gettingResponseList}>
                        </input>
                        <label id="label" className="label-top" htmlFor="toggle_unsubmitted">
                            {this.state.gettingResponseList ? t('Loading responses...') : t('Include un-submitted')}
                        </label>
                    </div>

                    <div className="react-table">
                        <ReactTable
                            className="ReactTable"
                            data={filteredResponses}
                            columns={columns}
                            minRows={0}
                        />
                    </div>
                </div>

                <form>
                    <div className="card">
                    <p className="h4 text-center mb-4">{t("Assign Reviewer")}</p>

                    <div className="row">
                        <p className="h6 text-center mb-3">{t("Filter the table above then enter a reviewer's email to assign them the filtered rows (the reviewer must already have a Baobab account)")}</p>
                        
                        <div className="col-md-10 pr-2">
                            <FormTextBox
                                id={"newReviewEmail"}
                                name={'newReviewEmail'}
                                placeholder={t("Email")}
                                onChange={this.handleChange}
                                value={newReviewerEmail}
                                key={"newReviewEmail"} />
                        </div>
                        <div className="col-md-2 pr-2">
                            <button
                                className="btn btn-primary btn-block"
                                onClick={() => { this.assignReviewer() }}
                                disabled={!newReviewerEmail}>
                                {t("Assign")}
                            </button>
                        </div>

                        {reviewerAssignError && <span className="alert alert-danger">
                            {JSON.stringify(this.state.reviewerAssignError)}
                        </span>}

                        {reviewerAssignSuccess && <span className="alert alert-success">
                            <Trans i18nKey="reviewsAssigned">Assigned {{numReviewsAssigned}} reviews to {{assignedReviewerEmail}}</Trans>
                        </span>}
                    </div>
                    </div>
                </form>

                <TagSelectorDialog
                    tags={this.state.filteredTags}
                    visible={this.state.tagSelectorVisible}
                    onCancel={() => this.setState({ tagSelectorVisible: false })}
                    onSelectTag={this.onSelectTag}
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

            </div>
        );
    }
}

export default withTranslation()(ResponseListComponent);
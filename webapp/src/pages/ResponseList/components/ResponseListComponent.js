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
            tags: [],
            tagSelectorVisible: false,
            confirmRemoveTagVisible: false,
            selectedResponse: null,
            error: null,
            loading: true,
            nameSearch : "",
            tagSearch : [],
            emailSearch: "",
            gettingResponseList: false,
            page: 0,
            pages: 0,
            perPage: 10
        }
    }


    componentDidMount() {
        this.getResponseList(this.state.page, this.state.perPage);
    }

    getResponseList = (page, perPage) => {
        this.setState({ gettingResponseList: true });

        const { includeUnsubmitted, nameSearch, emailSearch, tagSearch } = this.state;
        const tagId = tagSearch.length > 0 && this.state.tags ? this.state.tags.find(t => t.name === tagSearch[0]).id : null;

        Promise.all([
            tagsService.getTagList(this.props.event.id),
            responsesService.getResponseList(this.props.event.id, includeUnsubmitted, [], page + 1, perPage, nameSearch, emailSearch, tagId)
        ]).then(([tagsResponse, responsesResponse]) => {
            this.setState({
                tags: tagsResponse.tags,
                responses: responsesResponse.responses || [],
                page: responsesResponse.pagination ? responsesResponse.pagination.page - 1 : 0,
                pages: responsesResponse.pagination ? responsesResponse.pagination.pages : 0,
                perPage: responsesResponse.pagination ? responsesResponse.pagination.per_page : 10,
                error: tagsResponse.error || responsesResponse.error,
                loading: false,
                gettingResponseList: false
            });
        });
    }

    toggleUnsubmitted = () => {
        this.setState({
            includeUnsubmitted: !this.state.includeUnsubmitted
        }, () => this.getResponseList(0, this.state.perPage));
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
        this.setState({
          selectedResponse: response,
          tagSelectorVisible: true
        })
    }

    onSelectTag = (tag) => {
        responsesService.tagResponse(this.state.selectedResponse.response_id, tag.id, this.props.event.id)
        .then(resp => {
            if (resp.status === 201) {
                this.setState({
                    tagSelectorVisible: false,
                    selectedResponse: null
                }, () => this.getResponseList(this.state.page, this.state.perPage));
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
        this.setState({
          confirmRemoveTagVisible: false
        }, () => this.getResponseList(this.state.page, this.state.perPage));
      }
      else {
        this.setState({
          error: resp.error,
          confirmRemoveTagVisible: false
        });
      }
    })
  }

    handlePageChange = (page) => {
        this.getResponseList(page, this.state.perPage);
    }

    handlePageSizeChange = (perPage) => {
        this.getResponseList(0, perPage);
    }

    updateTagSearch = (selectedOption) => {
        this.setState({ tagSearch: selectedOption ? [selectedOption.value] : [] });
    }

    getSearchTags(tags) {
      return tags ? tags.filter(t=>t).map(t => ({ value: t.name, label: t.name})) : tags;
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
            reviewerAssignSuccess
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
            Cell: props => <div className="tags">
              {props.original.tags.map(t => 
                  <span className="tag badge badge-primary" onClick={()=>this.removeTag(props.original, t)} key={`tag_${props.original.response_id}_${t.id}`}>{t.name}</span>)}
              <i className="fa fa-plus-circle" onClick={() => this.addTag(props.original)}></i>
            </div>,
            accessor: u => u.tags.map(t => t.name).join("; "),
            minWidth: 150
          },
          {
            id: "language",
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
                            onChange={e => this.setState({ nameSearch: e.target.value })}
                            name=""
                            value={this.state.nameSearch} />
                        </div>

                        <div className={threeColClassName}>
                          <label className="col-form-label" htmlFor="EmailFilter">{t("Filter by email")}</label>
                            <FormTextBox
                            id="EmailFilter"
                            type="text"
                            placeholder="Search"
                            onChange={e => this.setState({ emailSearch: e.target.value })}
                            defaultValue={this.state.emailSearch} />
                        </div>

                        <div className={threeColClassName}>
                            <label className="col-form-label" htmlFor="TagFilter">{t("Filter by tag")}</label>
                            <Select
                              isClearable={true}
                              components={animatedComponents}
                              options={this.getSearchTags(this.state.tags)}
                              id="TagFilter"
                              placeholder="Search"
                              onChange={this.updateTagSearch}/>
                        </div>
                         <div className={threeColClassName}>
                            <label className="col-form-label">&nbsp;</label>
                            <button className="btn btn-primary form-control" onClick={() => this.getResponseList(0, this.state.perPage)}>{t("Search")}</button>
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
                            data={this.state.responses}
                            columns={columns}
                            manual
                            loading={this.state.gettingResponseList}
                            pages={this.state.pages}
                            page={this.state.page}
                            onPageChange={this.handlePageChange}
                            onPageSizeChange={this.handlePageSizeChange}
                            defaultPageSize={this.state.perPage}
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

                {this.state.tagSelectorVisible && <TagSelectorDialog
                    tags={this.state.tags.filter(t => !this.state.selectedResponse.tags.map(t=>t.id).includes(t.id) && this.assignable_tag_types.includes(t.tag_type))}
                    visible={this.state.tagSelectorVisible}
                    onCancel={() => this.setState({ tagSelectorVisible: false })}
                    onSelectTag={this.onSelectTag}
                />}

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
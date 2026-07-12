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
import { ConfirmModal } from "../../../components/Modal";
import TagSelectorDialog from '../../../components/TagSelectorDialog';

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
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            );
          }

        const columns = [{
            id: "response_link",
            Header: <div className="response-link text-left font-bold">{t("ID")}</div>,
            accessor: u => <NavLink
                        to={`/${this.props.event.key}/responsePage/${u.response_id}`}
                        className="text-primary hover:underline font-semibold">
                        {u.response_id}
                        </NavLink>,
            minWidth: 50
        }, {
            id: "user",
            Header: <div className="response-fullname text-left font-bold">{t("Full Name")}</div>,
            accessor: u =>
              <div className="response-fullname font-medium text-foreground">
                {u.user_title + " " + u.firstname + " " + u.lastname}
              </div>,
            minWidth: 150
        }, {
            id: "email",
            Header: <div className="response-email text-left font-bold">{t("Email")}</div>,
            accessor: u => u.email,
            minWidth: 150
        }, {
            id: "tags",
            Header: <div className="response-tags text-left font-bold">{t("Tags")}</div>,
            Cell: props => <div className="tags flex flex-wrap gap-1 items-center">
              {props.original.tags.map(t => 
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 cursor-pointer select-none" onClick={()=>this.removeTag(props.original, t)} key={`tag_${props.original.response_id}_${t.id}`}>{t.name}</span>)}
              <i className="fa fa-plus-circle text-primary hover:text-primary/80 transition-colors text-base cursor-pointer ml-1" onClick={() => this.addTag(props.original)}></i>
            </div>,
            accessor: u => u.tags.map(t => t.name).join("; "),
            minWidth: 150
          },
          {
            id: "language",
            Header: <div className="response-language text-left font-bold">{t("Language")}</div>,
            accessor: u => u.language,
            minWidth: 80
          },
          {
            id: "start_date",
            Header: <div className="response-start-date text-left font-bold">{t("Start Date")}</div>,
            accessor: u => u.start_date,
            minWidth: 150
          },
          {
            id: "is_submitted",
            Header: <div className="response-submitted text-left font-bold">{t("Submitted")}</div>,
            accessor: u => u.is_submitted ? "True" : "False",
            minWidth: 80
          },
          {
            id: "is_withdrawn",
            Header: <div className="response-withdrawn text-left font-bold">{t("Withdrawn")}</div>,
            accessor: u => u.is_withdrawn ? "True" : "False",
            minWidth: 80
          },
          {
            id: "submitted_date",
            Header: <div className="response-submitted-date text-left font-bold">{t("Submitted Date")}</div>,
            accessor: u => u.submitted_date,
            minWidth: 150
          },
          {
            id: "reviewers",
            Header: <div className="response-reviewers text-left font-bold">{t("Reviewers")}</div>,
            accessor: u => u.reviewers.filter(r=>r).map(r=>r.reviewer_name).join("; "),
            minWidth: 300
          }
        ];

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">

                {error && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                        {JSON.stringify(error)}
                    </div>
                )}

                <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6" key="response-table">
                    <h1 className="font-heading text-2xl font-bold text-foreground mb-6">{t("Response List")}</h1>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div className="space-y-2">
                            <label className="block text-sm font-semibold text-foreground/90" htmlFor="NameFilter">{t("Filter by name")}</label>
                            <FormTextBox
                                id="NameFilter"
                                type="text"
                                placeholder="Search"
                                onChange={e => this.setState({ nameSearch: e.target.value })}
                                name=""
                                value={this.state.nameSearch}
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="block text-sm font-semibold text-foreground/90" htmlFor="EmailFilter">{t("Filter by email")}</label>
                            <FormTextBox
                                id="EmailFilter"
                                type="text"
                                placeholder="Search"
                                onChange={e => this.setState({ emailSearch: e.target.value })}
                                defaultValue={this.state.emailSearch}
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="block text-sm font-semibold text-foreground/90" htmlFor="TagFilter">{t("Filter by tag")}</label>
                            <Select
                                isClearable={true}
                                components={animatedComponents}
                                options={this.getSearchTags(this.state.tags)}
                                id="TagFilter"
                                placeholder="Search"
                                onChange={this.updateTagSearch}
                            />
                        </div>

                        <div className="flex items-end pb-5">
                            <button className="w-full inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm cursor-pointer h-[46px]" onClick={() => this.getResponseList(0, this.state.perPage)}>{t("Search")}</button>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                        <input 
                            onClick={(e) => this.toggleUnsubmitted()}
                            className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer"
                            type="checkbox"
                            value=""
                            id="toggle_unsubmitted"
                            disabled={this.state.gettingResponseList}
                        />
                        <label className="text-sm font-medium text-foreground cursor-pointer select-none" htmlFor="toggle_unsubmitted">
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

                <form onSubmit={e => e.preventDefault()}>
                    <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
                        <h3 className="text-lg font-bold text-foreground/90">{t("Assign Reviewer")}</h3>
                        <p className="text-sm text-muted-foreground">{t("Filter the table above then enter a reviewer's email to assign them the filtered rows (the reviewer must already have a Baobab account)")}</p>
                        
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                            <div className="md:col-span-3">
                                <FormTextBox
                                    id={"newReviewEmail"}
                                    name={'newReviewEmail'}
                                    placeholder={t("Email")}
                                    onChange={this.handleChange}
                                    value={newReviewerEmail}
                                    key={"newReviewEmail"}
                                />
                            </div>
                            <div className="pb-5">
                                <button
                                    type="button"
                                    className="w-full inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm cursor-pointer h-[46px]"
                                    onClick={() => { this.assignReviewer() }}
                                    disabled={!newReviewerEmail}
                                >
                                    {t("Assign")}
                                </button>
                            </div>
                        </div>

                        {reviewerAssignError && (
                            <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">
                                {JSON.stringify(this.state.reviewerAssignError)}
                            </div>
                        )}

                        {reviewerAssignSuccess && (
                            <div className="bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl text-sm w-full text-center mt-4">
                                <Trans i18nKey="reviewsAssigned">Assigned {{numReviewsAssigned}} reviews to {{assignedReviewerEmail}}</Trans>
                            </div>
                        )}
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
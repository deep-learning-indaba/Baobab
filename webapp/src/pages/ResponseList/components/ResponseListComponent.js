import React, { Component } from 'react';
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
import FormSelect from "../../../components/form/FormSelect";
import { createColClassName } from "../../../utils/styling/styling";

class ResponseListForm extends Component {
    constructor(props) {
        super(props);
        this.state = {
            btnUpdate: false,
            includeUnsubmitted: false,
            responses: [],
            filteredResponses: [],
            tags: [],
            filteredTags: [],
            tagSelectorVisible: false,
            selectedResponse: null,
            error: null,
            loading: true,
            nameSearch : "",
            tagSearch : "",
            emailSearch: ""
        }
    }

    componentDidMount() {
        this.setState({ loading: true }, () => this.getResponseList());

    }

    getResponseList() {
        Promise.all([
            tagsService.getTagList(this.props.event.id),
            responsesService.getResponseList(this.props.event.id, false, []),
        ]).then(([tagsResponse, responsesResponse]) => {
            this.setState({
                tags: tagsResponse.tags,
                responses: responsesResponse.responses,
                filteredResponses : responsesResponse.responses,
                error: tagsResponse.error || responsesResponse.error,
                loading: false
            }, this.handleData);
        });
    }

    refreshResponses() {
        const { includeUnsubmitted } = this.state;

        responsesService.getResponseList(this.props.event.id, includeUnsubmitted, []).then(resp => {
            this.setState({
                responses: resp.responses,
                error: resp.error
            }, this.handleData);
        });
    }

    // Handle/Format Data
    handleData = () => {
        const { responses } = this.state;
        console.log(responses);


        if (!responses) {
            console.log('ERROR: responses is not defined: ', responses);
            return;
        }

        // TODO: Change this to a map and don't mutate the state. 
        responses.forEach(val => {
            let handleReviews = [];
            let handleTags = [];

            // Create Response Id Link
            if (this.props.event) {
                val.response_link = <NavLink
                    to={`/${this.props.event.key}/responsePage/${val.response_id}`}
                    className="table-nav-link"
                >
                    {val.response_id}
                </NavLink>;
            }

            // tags
            const tagCell = <div key={'tags_{val.response_id}'}>
                {val.tags.map(tag => {
                    return <span className="tag badge badge-primary" onClick={()=>this.removeTag(val, tag)} key={`tag_${val.response_id}_${tag.id}`}>{tag.name}</span>
                })}
                <i className="fa fa-plus-circle" onClick={() => this.addTag(val)}></i>
            </div>
            handleTags.push(tagCell);

            // extract only the reviewers name
            val.reviewers.forEach(review => {
                review ? handleReviews.push(review.reviewer_name) : handleReviews.push("");
            })

            // add User Title as new column 
            function userTitleCol(row, user_title, firstname, lastname) {
                return row.user = user_title + " " + firstname + " " + lastname;
            }

            // envoke and store new columns for UserTitle
            // combine user credentials
            userTitleCol(val, val.user_title, val.firstname, val.lastname);

            // insert new reviews values as columns
            if (handleReviews.length) {
                handleReviews.forEach((review, index) => {
                    let num = (index) + (1);
                    let key = this.props.t("Reviewer") + " " + num;
                    val[key] = review;
                    handleReviews = [];
                })
            };

            val.tags = handleTags;
            val.is_submitted = val.is_submitted ? "True" : "False";
            val.is_withdrawn = val.is_withdrawn ? "True" : "False";

            // delete original review and answer rows as they don't need to be displayed with all their data
            delete val.reviewers;
            delete val.user_title;
            delete val.firstname;
            delete val.lastname;

        })

        this.setState({
            responseTable: responses,
            btnUpdate: false
        });
    }

    generateColumns() {
        const t = this.props.t;
        const columns = [{
            id: "user",
            Header: <div className="invitedguest-fullname">{t("Full Name")}</div>,
            accessor: u =>
              <div className="invitedguest-fullname">
                {u.user.user_title + " " + u.user.firstname + " " + u.user.lastname}
              </div>,
            minWidth: 150
          }, {
            id: "email",
            Header: <div className="invitedguest-email">{t("Email")}</div>,
            accessor: u => u.user.email
          }, {
            id: "role",
            Header: <div className="invitedguest-role">{t("Role")}</div>,
            accessor: u => u.role
          }, {
            id: "tags",
            Header: <div className="invitedguest-tags">{t("Tags")}</div>,
            Cell: props => <div>
              {props.original.tags.map(t => 
                  <span className="tag badge badge-primary" onClick={()=>this.removeTag(props.original, t)} key={`tag_${props.original.invited_guest_id}_${t.id}`}>{t.name}</span>)}
              <i className="fa fa-plus-circle" onClick={() => this.addTag(props.original)}></i>
            </div>,
            accessor: u => u.tags.map(t => t.name).join("; ")
          }];

        return columns;
    }

    // Generate table columns
    generateCols() {
        let colFormat = [];
        // Find the row with greatest col count and assign the col values to React Table
        if (this.state.responseTable) {

            // function
            function readColumns(rows) {
                let tableColumns = ["response_link", "user", "email", "tags", "start_date", "is_submitted", "is_withdrawn", "submitted_date"];
                rows.map(val => {
                    let newColumns = Object.keys(val);
                    newColumns.forEach(val => {
                        if (!tableColumns.includes(val)) {
                            tableColumns.push(val)
                        };
                    });
                });
                return tableColumns
            };

            // function
            function widthCalc(colItem) {

                if (colItem.includes('user') || colItem.includes('Review') || colItem.includes('date') || colItem.includes('email')) {
                    return 180
                }
                else {
                    return 100
                }
            }

            let col = readColumns(this.state.responseTable);
            
            // TODO: Make columns deterministic, add translations for headers
            colFormat = col.map(function (val) {
                return { id: val, Header: val, accessor: val, className: "myCol", filterable: false, width: widthCalc(val) }
            });
        }
        return colFormat
    }

    // Reset state and tag list UI 
    reset() {
        // reset checkboxes
        document.querySelectorAll('input[type=checkbox]').forEach(el => el.checked = false);
    }

    toggleUnsubmitted = () => {
        this.setState({
            includeUnsubmitted: !this.state.includeUnsubmitted
        }, () => this.refreshResponses());
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
                    this.refreshResponses();
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
          filteredTags: this.state.tags.filter(t=>!tagIds.includes(t.id))
        })
    }

    onSelectTag = (tag) => {
        responsesService.tagResponse(this.state.selectedResponse.response_id, tag.id, this.props.event.id)
        .then(resp => {
            if (resp.statusCode === 201) {
                const newResponse = {
                ...this.state.selectedResponse,
                tags: [...this.state.selectedResponse.tags, resp.response.data]
                } 
                const newResponses = this.state.responses.map(r => 
                    r.response_id === this.state.selectedResponse.response_id  ? newResponse : r);
                this.setState({
                tagSelectorVisible: false,
                selectedResponse: null,
                filteredTags: [],
                responses: newResponses
                }, () => this.filterResponses);
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
      if (resp.statusCode === 204) {
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
        this.setState({tagSearch: event.value}, this.filterResponses);
    }

    filterResponses = () => {
        const { nameSearch, tagSearch, emailSearch } = this.state;
        const filtered = this.state.responses.filter(r => {
            console.log(r);
          let passed = true;
          if (nameSearch) {
            passed = r.user.toLowerCase().indexOf(nameSearch.toLowerCase()) > -1;
          }
          if (emailSearch && passed) {
            passed = r.email.toLowerCase().indexOf(emailSearch.toLowerCase()) > -1;
          }
          if (tagSearch && passed && tagSearch !== "all") {
            passed = r.tag === tagSearch;
          }
          return passed;
        });
        this.setState({ filteredResponses: filtered });
      }

    render() {
        const threeColClassName = createColClassName(12, 4, 4, 4);  //xs, sm, md, lg
        const twoColClassName = createColClassName(12, 6, 6, 6);  //xs, sm, md, lg
        const t = this.props.t;

        // State values
        const {
            error,
            loading,
            numReviewsAssigned,
            assignedReviewerEmail,
            reviewerAssignError,
            newReviewerEmail,
            reviewerAssignSuccess,
            tags,
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

        // Generate Col
        const columns = this.generateCols();

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
                            <FormTextBox
                            id="NameFilter"
                            type="text"
                            placeholder="Search"
                            onChange={this.updateNameSearch}
                            label={t("Filter by name")}
                            name=""
                            value={this.state.nameSearch} />
                        </div>

                        <div className={threeColClassName}>
                            <FormTextBox
                            id="EmailFilter"
                            type="text"
                            placeholder="Search"
                            onChange={this.updateEmailSearch}
                            label={t("Filter by email")}
                            defaultValue={this.state.emailSearch} />
                        </div>

                        <div className={threeColClassName}>
                            <FormSelect
                            options={tags}
                            id="TagFilter"
                            placeholder="Search"
                            onChange={this.updateTagSearch}
                            label={t("Filter by tag")}
                            defaultValue={this.state.tagSearch || "all"} />
                        </div>
                    </div>
                    
                    <div className="checkbox-top">
                        <input onClick={(e) => this.toggleUnsubmitted()} className="form-check-input input" type="checkbox" value="" id="defaultCheck1" />
                        <label id="label" className="label-top" htmlFor="defaultCheck1">
                            {t('Include un-submitted')}
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
                        <p className="h6 text-center mb-3">{t("Filter the table above then enter an email to assign a reviewer to the filtered rows (the reviewer must already have a Baobab account)")}</p>
                        
                        <div className={twoColClassName}>
                            <FormTextBox
                                id={"newReviewEmail"}
                                name={'newReviewEmail'}
                                placeholder={t("Email")}
                                onChange={this.handleChange}
                                value={newReviewerEmail}
                                key={"newReviewEmail"} />
                        </div>
                        <div className={twoColClassName}>
                            <button
                                class="btn btn-primary stretched"
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
        )
    }
}

export default withTranslation()(ResponseListForm);
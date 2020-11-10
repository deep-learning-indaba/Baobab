import React, { Component } from 'react';
import { reviewService } from '../../../services/reviews/review.service';

class ReviewModal extends Component {
    constructor(props) {
        super(props);
        this.state = {
            selectedReviews: []
        }
    };


    renderReviewers() {
        reviewService.getReviewAssignments(this.props.event.id).then(response => {
            console.log(response)
        })
    }


    handleSelect(reviewer) {
        const updateReviews = this.state.selectedReviews;
        
        if (updateReviews.includes(reviewer)) {
            updateReviews.splice(updateReviews.indexOf(reviewer), 1)
        }
        else {
            updateReviews.push(reviewer)
        }

        this.setState({
            selectedReviews: updateReviews
        })
    }



    renderModal() {
        const { selectedReviews } = this.state;
        
        const { reviewers, handlePost, t } = this.props
       

        if (this.props.event) {
            return (
                <div className="modal fade" id="exampleModalReview" tabIndex="-1" role="dialog" aria-labelledby="exampleModalReview" aria-hidden="true">
                    <div className="modal-dialog" role="document">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title" id="exampleModalLabel">{t('Reviewers')}</h5>
                                <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>

                            <div className="modal-body">
                                {reviewers && reviewers.map(val => {
                                    return <button onClick={(e) => this.handleSelect(val)}
                                        className={selectedReviews.includes(val) ? "review-select active" : "review-select"}
                                        key={val.reviewer_user_id}
                                    >
                                        <label> {val.user_title} {val.firstname} {val.lastname} </label>
                                        
                                        <div>
                                        <p>Reviews Allocated: {val.reviews_allocated} </p>
                                        <p>Reviews Completed: {val.reviews_completed} </p>
                                        </div>

                                    </button>
                                })}


                            </div>
                            <div className="modal-footer">
                                <button type="button"
                                    className="btn btn-secondary"
                                    data-dismiss="modal"
                                >
                                    {t('Cancel')}
                                </button>
                                <button
                                    type="button"
                                    data-dismiss="modal"
                                    className="btn btn-primary"
                                    onClick={(e) => handlePost(selectedReviews)}
                                >
                                    {t('Post')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )
        }
    }


    render() {
        const modal = this.renderModal()
        return (
            <div>
                {modal}
            </div>
        )
    }
}

export default ReviewModal
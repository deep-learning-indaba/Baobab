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


    handleSelect(key) {
        const updateReviews = this.state.selectedReviews;

        if (updateReviews.includes(key)) {
            updateReviews.splice(updateReviews.indexOf(key), 1)
        }
        else {
            updateReviews.push(key.toString())
        }

        this.setState({
            selectedReviews: updateReviews
        })

    }



    renderModal() {
        const { selectedReviews } = this.state;
        // Translation
        const t = this.props.t;

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

                                {this.props.reviews.map(val => {
                                    return <div onClick={(e) => this.handleSelect(val.email)}
                                        className={selectedReviews.includes(val.email) ? "review-select active" : "review-select"}
                                        key={val.email}
                                    >
                                        <h5> {val.user_title}{val.firstname}{val.lastname} </h5>
                                        <span>Reviews Allocated: {val.reviews_allocated} </span>
                                        <span>Reviews Completed: {val.reviews_completed} </span>
                                    </div>
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
                                    onClick={(e) => this.renderReviewers(e)}
                                >
                                    {t('Save')}
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
import React, { Component } from "react";

class ReviewModal extends Component {
  constructor(props) {
    super(props);
    this.state = {
      selectedReviewer: null,
    };
  }

  handlePost(reviewers) {
    this.props.handlePost(reviewers);

    this.setState({
      selectedReviewer: null,
    });
  }

  handleSelect(reviewer) {
    this.setState({
      selectedReviewer: reviewer,
    });
  }

  renderModal() {
    const { selectedReviewer } = this.state;

    const { reviewers, t } = this.props;

    if (this.props.event) {
      return (
        <div
          className="modal fade"
          id="exampleModalReview"
          tabIndex="-1"
          role="dialog"
          aria-labelledby="exampleModalReview"
          aria-hidden="true"
        >
          <div className="modal-dialog" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title" id="exampleModalLabel">
                  {t("Reviewers")}
                </h5>
                <button
                  type="button"
                  className="close"
                  data-dismiss="modal"
                  aria-label="Close"
                >
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>

              <div className="modal-body">
                {reviewers &&
                  reviewers.map((val) => {
                    return (
                      <button
                        onClick={(e) => this.handleSelect(val)}
                        className={
                          selectedReviewer === val
                            ? "review-select active"
                            : "review-select"
                        }
                        key={val.reviewer_user_id}
                      >
                        <label>
                          {" "}
                          {val.user_title} {val.firstname} {val.lastname}{" "}
                        </label>
                        <div class="reviewer-email">{val.email}</div>
                        <div>
                          <p>
                            {" "}
                            {t("Reviews Allocated")} : {val.reviews_allocated}{" "}
                          </p>
                          <p>
                            {" "}
                            {t("Reviews Completed")} : {val.reviews_completed}{" "}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                {!reviewers && (
                  <span>{t("There are no more reviewers available")}</span>
                )}
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  data-dismiss="modal"
                >
                  {t("Cancel")}
                </button>
                <button
                  type="button"
                  data-dismiss="modal"
                  className="btn btn-primary"
                  onClick={(e) => this.handlePost(selectedReviewer)}
                >
                  {t("Assign")}
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }
  }

  render() {
    const modal = this.renderModal();
    return <div>{modal}</div>;
  }
}

export default ReviewModal;

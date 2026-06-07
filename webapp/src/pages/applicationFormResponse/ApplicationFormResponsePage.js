import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import FormResponseDetailComponent from '../formResponseDetail/components/FormResponseDetailComponent';
import { formResponseService } from '../../services/formResponse';
import { tagsService } from '../../services/tags/tags.service';
import { outcomeService } from '../../services/outcome/outcome.service';
import { ConfirmModal } from '../../components/Modal';
import TagSelectorDialog from '../../components/TagSelectorDialog';
import FormTextBox from '../../components/form/FormTextBox';
import moment from 'moment';

const OUTCOME_OPTIONS = {
  JOURNAL: [
    { value: 'ACCEPTED', label: 'Accept' },
    { value: 'ACCEPT_W_REVISION', label: 'Accept with Minor Revision' },
    { value: 'REJECT_W_ENCOURAGEMENT', label: 'Reject with Encouragement to Resubmit' },
    { value: 'REJECTED', label: 'Reject' }
  ],
  CALL: [
    { value: 'ACCEPTED', label: 'Accept' },
    { value: 'REJECTED', label: 'Reject' }
  ],
  EVENT: [
    { value: 'REJECTED', label: 'Reject' },
    { value: 'WAITLIST', label: 'Waitlist' }
  ]
};

function outcomeVariant(status) {
  if (status === 'ACCEPTED') return 'bg-green-50 text-green-700 border-green-200';
  if (status === 'REJECTED') return 'bg-error/10 text-error border-error/20';
  return 'bg-amber-50 text-amber-700 border-amber-200';
}

class ApplicationFormResponsePage extends Component {
  constructor(props) {
    super(props);
    this.state = {
      allTags: [],
      outcome: null,
      reviewers: [],
      reviewerEmail: '',
      tagSelectorVisible: false,
      confirmRemoveTagVisible: false,
      confirmRemoveReviewerVisible: false,
      tagToRemove: null,
      reviewerToRemove: null,
      error: null,
      reviewerError: null,
      reviewerSuccess: false,
      assigningReviewer: false,
    };
  }

  getFormId() {
    return this.props.formId || (this.props.match && this.props.match.params.formId);
  }

  getResponseId() {
    return this.props.responseId || (this.props.match && this.props.match.params.responseId);
  }

  loadAdminData = (response) => {
    const { event } = this.props;
    if (!event || !response) return;
    const formId = this.getFormId();
    const responseId = response.id;

    Promise.all([
      tagsService.getTagList(event.id),
      outcomeService.getOutcome(event.id, response.user_id),
      formResponseService.getResponseReviews(formId, responseId, event.id)
    ]).then(([tagsRes, outcomeRes, reviewsRes]) => {
      this.setState({
        allTags: tagsRes.tags || [],
        outcome: outcomeRes.status === 200 ? outcomeRes.outcome : null,
        reviewers: reviewsRes.reviews || []
      });
    });
  };

  onAddTag = (tag) => {
    const { event } = this.props;
    const formId = this.getFormId();
    const responseId = this.getResponseId();
    formResponseService.tagFormResponse(formId, responseId, event.id, tag.id)
      .then(res => {
        this.setState({ tagSelectorVisible: false });
        if (!res.error && this._reloadData) this._reloadData();
        else if (res.error) this.setState({ error: res.error });
      });
  };

  onConfirmRemoveTag = () => {
    const { event } = this.props;
    const formId = this.getFormId();
    const responseId = this.getResponseId();
    formResponseService.removeFormResponseTag(formId, responseId, event.id, this.state.tagToRemove)
      .then(res => {
        this.setState({ confirmRemoveTagVisible: false, tagToRemove: null });
        if (!res.error && this._reloadData) this._reloadData();
        else if (res.error) this.setState({ error: res.error });
      });
  };

  onUpdateStatus = (is_submitted, is_withdrawn) => {
    const { event } = this.props;
    const formId = this.getFormId();
    const responseId = this.getResponseId();
    const patch = {};
    if (is_submitted !== undefined) patch.is_submitted = is_submitted;
    if (is_withdrawn !== undefined) patch.is_withdrawn = is_withdrawn;
    formResponseService.adminUpdateResponseStatus(formId, responseId, event.id, patch)
      .then(res => {
        if (!res.error && this._reloadData) this._reloadData();
        else if (res.error) this.setState({ error: res.error });
      });
  };

  onAssignOutcome = (outcomeValue) => {
    const { event } = this.props;
    const userId = this._currentResponse && this._currentResponse.user_id;
    outcomeService.assignOutcome(userId, event.id, outcomeValue)
      .then(res => {
        if (res.status === 201) this.setState({ outcome: res.outcome });
        else this.setState({ error: res.error });
      });
  };

  onAssignReviewer = () => {
    const { event } = this.props;
    const formId = this.getFormId();
    const responseId = this.getResponseId();
    const email = this.state.reviewerEmail.trim();
    if (!email) return;
    this.setState({ assigningReviewer: true, reviewerError: null, reviewerSuccess: false });
    formResponseService.assignResponseReviewer(formId, responseId, event.id, email)
      .then(res => {
        if (!res.error) {
          this.setState({
            reviewers: [...this.state.reviewers, res.reviewer],
            reviewerEmail: '',
            reviewerSuccess: true,
            assigningReviewer: false
          });
        } else {
          this.setState({ reviewerError: res.error, assigningReviewer: false });
        }
      });
  };

  onConfirmRemoveReviewer = () => {
    const { event } = this.props;
    const formId = this.getFormId();
    const responseId = this.getResponseId();
    formResponseService.removeResponseReviewer(formId, responseId, event.id, this.state.reviewerToRemove)
      .then(res => {
        if (!res.error) {
          this.setState(prev => ({
            reviewers: prev.reviewers.filter(r => r.reviewer_user_id !== prev.reviewerToRemove),
            confirmRemoveReviewerVisible: false,
            reviewerToRemove: null
          }));
        } else {
          this.setState({ error: res.error, confirmRemoveReviewerVisible: false });
        }
      });
  };

  renderStatusPanel(response, t) {
    const { is_submitted, is_withdrawn } = response;
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-border p-5 space-y-3">
        <h3 className="font-bold text-sm text-foreground">{t('Response Status')}</h3>
        <div className="flex flex-wrap gap-2">
          {is_withdrawn && (
            <button onClick={() => this.onUpdateStatus(undefined, false)}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
              {t('Un-withdraw')}
            </button>
          )}
          {!is_withdrawn && is_submitted && (
            <>
              <button onClick={() => this.onUpdateStatus(false, undefined)}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-border text-foreground hover:bg-surface-high transition-colors">
                {t('Un-submit')}
              </button>
              <button onClick={() => this.onUpdateStatus(undefined, true)}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-error/10 text-error border border-error/20 hover:bg-error/20 transition-colors">
                {t('Withdraw')}
              </button>
            </>
          )}
          {!is_withdrawn && !is_submitted && (
            <>
              <button onClick={() => this.onUpdateStatus(true, undefined)}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
                {t('Submit')}
              </button>
              <button onClick={() => this.onUpdateStatus(undefined, true)}
                      className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-error/10 text-error border border-error/20 hover:bg-error/20 transition-colors">
                {t('Withdraw')}
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  renderTagsPanel(response, t) {
    const { allTags } = this.state;
    const responseTags = response.tags || [];
    const assignableTags = allTags.filter(tag =>
      tag.tag_type === 'RESPONSE' && !responseTags.some(rt => rt.id === tag.id)
    );

    return (
      <div className="bg-white rounded-2xl shadow-sm border border-border p-5 space-y-3">
        <h3 className="font-bold text-sm text-foreground">{t('Tags')}</h3>
        <div className="flex flex-wrap gap-1.5">
          {responseTags.map(tag => (
            <span
              key={tag.id}
              onClick={() => this.setState({ confirmRemoveTagVisible: true, tagToRemove: tag.id })}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 cursor-pointer hover:bg-primary/20 transition-colors"
            >
              {tag.name} ×
            </span>
          ))}
          <button
            onClick={() => this.setState({ tagSelectorVisible: true })}
            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border border-dashed border-primary/40 text-primary hover:bg-primary/5 transition-colors"
          >
            + {t('Add tag')}
          </button>
        </div>

        {this.state.tagSelectorVisible && (
          <TagSelectorDialog
            tags={assignableTags}
            visible={this.state.tagSelectorVisible}
            onCancel={() => this.setState({ tagSelectorVisible: false })}
            onSelectTag={this.onAddTag}
          />
        )}
        <ConfirmModal
          visible={this.state.confirmRemoveTagVisible}
          onOK={this.onConfirmRemoveTag}
          onCancel={() => this.setState({ confirmRemoveTagVisible: false, tagToRemove: null })}
          okText={t('Yes')}
          cancelText={t('No')}
        >
          <p>{t('Are you sure you want to remove this tag?')}</p>
        </ConfirmModal>
      </div>
    );
  }

  renderOutcomePanel(response, t) {
    const eventType = this.props.event && this.props.event.event_type;
    const outcomeOptions = OUTCOME_OPTIONS[eventType] || [];
    const { outcome } = this.state;

    if (!response.is_submitted || response.is_withdrawn) return null;

    return (
      <div className="bg-white rounded-2xl shadow-sm border border-border p-5 space-y-3">
        <h3 className="font-bold text-sm text-foreground">{t('Outcome')}</h3>
        {outcome && outcome.status && outcome.status !== 'REVIEW' ? (
          <div className="space-y-2">
            <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold border ${outcomeVariant(outcome.status)}`}>
              {outcome.status}
            </span>
            {outcome.timestamp && (
              <p className="text-xs text-muted-foreground">{moment(outcome.timestamp).format('D MMM YYYY, H:mm')}</p>
            )}
          </div>
        ) : outcomeOptions.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {outcomeOptions.map(opt => (
              <button
                key={opt.value}
                onClick={() => this.onAssignOutcome(opt.value)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-border text-foreground hover:bg-surface-high transition-colors"
              >
                {t(opt.label)}
              </button>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">{t('No outcome options configured for this event type.')}</p>
        )}
      </div>
    );
  }

  renderReviewersPanel(t) {
    const { reviewers, reviewerEmail, reviewerError, reviewerSuccess, assigningReviewer } = this.state;

    return (
      <div className="bg-white rounded-2xl shadow-sm border border-border p-5 space-y-4">
        <h3 className="font-bold text-sm text-foreground">{t('Reviewers')}</h3>
        <div className="space-y-2">
          {reviewers.length === 0 && (
            <p className="text-xs text-muted-foreground">{t('No reviewers assigned.')}</p>
          )}
          {reviewers.map((r, i) => (
            <div key={r.reviewer_user_id} className="flex items-center justify-between text-sm">
              <div>
                <span className="font-medium">{r.user_title} {r.firstname} {r.lastname}</span>
                <span className={`ml-2 text-xs font-semibold ${r.is_submitted ? 'text-green-600' : 'text-muted-foreground'}`}>
                  {r.is_submitted ? t('Completed') : t('Not Started')}
                </span>
              </div>
              {!r.is_submitted && (
                <button
                  onClick={() => this.setState({ confirmRemoveReviewerVisible: true, reviewerToRemove: r.reviewer_user_id })}
                  className="text-muted-foreground hover:text-error transition-colors ml-2"
                  title={t('Remove reviewer')}
                >
                  <i className="far fa-trash-alt text-xs"></i>
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="space-y-2 pt-2 border-t border-border/40">
          <p className="text-xs font-semibold text-foreground/70">{t('Assign Reviewer')}</p>
          <FormTextBox
            id="reviewerEmail"
            name="reviewerEmail"
            placeholder={t('Reviewer email')}
            value={reviewerEmail}
            onChange={e => this.setState({ reviewerEmail: e.target.value, reviewerError: null, reviewerSuccess: false })}
          />
          <button
            onClick={this.onAssignReviewer}
            disabled={!reviewerEmail || assigningReviewer}
            className="w-full px-3 py-2 text-xs font-semibold rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {assigningReviewer ? t('Assigning...') : t('Assign')}
          </button>
          {reviewerError && (
            <p className="text-xs text-error">{reviewerError}</p>
          )}
          {reviewerSuccess && (
            <p className="text-xs text-green-600">{t('Reviewer assigned successfully.')}</p>
          )}
        </div>

        <ConfirmModal
          visible={this.state.confirmRemoveReviewerVisible}
          onOK={this.onConfirmRemoveReviewer}
          onCancel={() => this.setState({ confirmRemoveReviewerVisible: false, reviewerToRemove: null })}
          okText={t('Yes')}
          cancelText={t('No')}
        >
          <p>{t('Are you sure you want to remove this reviewer?')}</p>
        </ConfirmModal>
      </div>
    );
  }

  onResponseLoad = (response, form, reloadData) => {
    this._reloadData = reloadData;
    this._currentResponse = response;
    this.loadAdminData(response);
  };

  renderAdminContent = (response, form, reloadData) => {
    const { t } = this.props;

    return (
      <>
        {this.state.error && (
          <div className="bg-error/10 text-error border border-error/20 p-3 rounded-xl text-xs">
            {this.state.error}
          </div>
        )}
        {this.renderStatusPanel(response, t)}
        {this.renderTagsPanel(response, t)}
        {this.renderOutcomePanel(response, t)}
        {this.renderReviewersPanel(t)}
      </>
    );
  };

  render() {
    const formId = this.getFormId();
    const responseId = this.getResponseId();

    return (
      <FormResponseDetailComponent
        {...this.props}
        formId={formId}
        responseId={responseId}
        onResponseLoad={this.onResponseLoad}
        renderAdminContent={this.renderAdminContent}
      />
    );
  }
}

export default withTranslation()(ApplicationFormResponsePage);

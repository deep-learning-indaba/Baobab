import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import FormRenderer from "../formRenderer/FormRenderer";
import ResponseAnswers from "../../components/form/ResponseAnswers";
import Modal from "../../components/Modal";
import { Button } from "../../components/ui/button";
import { reviewService } from "../../services/reviews/review.service";
import { formResponseService } from "../../services/formResponse";
import { userService } from "../../services/user/user.service";
import { resolveContentLanguage } from "../../utils/eventLanguages";
import {
  STATUS, ReviewStatusBadge, identifierText, weightedScore, weightedQuestions, formatScore, PageMessage, Spinner,
} from "./reviewUtils";

function FlagModal({ visible, onClose, eventId, applicantUserId, t }) {
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const close = () => { setComment(''); setError(null); onClose(); };
  const save = () => {
    setSaving(true);
    userService.addComment(eventId, applicantUserId, comment).then(result => {
      setSaving(false);
      if (result.error) setError(result.error);
      else close();
    });
  };

  return (
    <Modal visible={visible} onClickBackdrop={close}>
      <h2 className="font-heading text-lg font-bold text-foreground">{t('Flag Response')}</h2>
      <p className="text-sm text-muted-foreground">
        {t('If reviewing this response revealed an issue that should be considered if this candidate were accepted, please describe it below.')}
      </p>
      <textarea className="w-full min-h-[120px] rounded-lg border border-border p-3 text-sm"
                value={comment} onChange={e => setComment(e.target.value)} />
      {error && <p className="text-sm text-error">{error}</p>}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={close}>{t('Cancel')}</Button>
        <Button onClick={save} disabled={saving || !comment.trim()}>
          {saving ? t('Saving...') : t('Add Flag')}
        </Button>
      </div>
    </Modal>
  );
}

/** Review one application: the application on one side, the review form on the other. */
export default function ReviewPage({ event, match, history }) {
  const { t, i18n } = useTranslation();
  const language = resolveContentLanguage(event, i18n.language);
  const reviewResponseId = match.params.reviewResponseId;

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [justSubmitted, setJustSubmitted] = useState(false);
  const [flagVisible, setFlagVisible] = useState(false);

  useEffect(() => {
    setData(null);
    setError(null);
    setJustSubmitted(false);
    reviewService.getAssignedReview(reviewResponseId, event.id, language).then(result => {
      if (result.error) setError(result.error);
      else setData(result.data);
      window.scrollTo(0, 0);
    });
  }, [reviewResponseId, event.id, language]);

  const reviewFormId = data && data.review_form.id;

  const save = useCallback(async ({ answers: formAnswers }) => {
    const result = await formResponseService.updateResponse(reviewFormId, reviewResponseId, { answers: formAnswers });
    if (result.error) return { success: false, error: result.error };
    return { success: true, data: result.response };
  }, [reviewFormId, reviewResponseId]);

  const submit = useCallback(async (formData) => {
    const saved = await save(formData);
    if (!saved.success) return saved;
    const result = await formResponseService.submitResponse(reviewFormId, reviewResponseId);
    if (result.error) {
      return { success: false, error: result.error, validationErrors: result.validationErrors };
    }
    setJustSubmitted(true);
    window.scrollTo(0, 0);
    return { success: true, data: result.response };
  }, [save, reviewFormId, reviewResponseId]);

  if (error) {
    return (
      <PageMessage icon="fa-exclamation-triangle" title={t('Review not available')} tone="error">
        <p>{error}</p>
        <Link to={`/${event.key}/reviews`} className="inline-block mt-3 font-semibold text-action hover:underline">
          {t('Return to review list')}
        </Link>
      </PageMessage>
    );
  }
  if (!data) return <Spinner />;

  const { navigation } = data;
  const nextId = navigation.next_review_response_id;
  const hasScore = weightedQuestions(data.review_form).length > 0;
  const liveScore = weightedScore(data.review_form, answers);
  const isSubmitted = justSubmitted || data.status === STATUS.SUBMITTED;
  const title = identifierText(data.identifiers, data.application_response.id, t);
  const goToNext = () => history.push(`/${event.key}/reviews/${nextId}`);

  return (
    <div className="w-full max-w-7xl mx-auto pt-6 px-4 space-y-5 text-left">
      <header className="flex flex-col lg:flex-row lg:items-start gap-4 justify-between">
        <div className="space-y-1 min-w-0">
          <Link to={`/${event.key}/reviews`} className="text-sm font-medium text-action hover:underline">
            ← {t('All reviews')}
          </Link>
          <h1 className="font-heading text-2xl font-bold text-foreground break-words">{title}</h1>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <ReviewStatusBadge status={isSubmitted ? STATUS.SUBMITTED : data.status} t={t} />
            {navigation.position && (
              <span>{t('Review {{position}} of {{total}}', { position: navigation.position, total: navigation.total })}</span>
            )}
            <span>·</span>
            <span>{t('{{count}} remaining', { count: navigation.remaining })}</span>
            <span>·</span>
            <span title={t('Please quote this in any correspondence with admins outside of the system.')}>
              {t('Response ID')}: <span className="font-semibold text-foreground">{data.application_response.id}</span>
            </span>
          </div>
        </div>
        <div className="flex flex-wrap lg:flex-nowrap items-center gap-2 lg:shrink-0 lg:pt-6">
          {hasScore && (
            <div className="px-4 py-1.5 rounded-xl bg-primary/5 border border-primary/20 text-sm whitespace-nowrap">
              {t('Total Score')}: <span className="font-black text-primary text-lg">{formatScore(liveScore)}</span>
            </div>
          )}
          <Button variant="outline" size="sm" onClick={() => setFlagVisible(true)}>
            <i className="fas fa-flag" />{t('Flag Response')}
          </Button>
          {nextId && !isSubmitted && (
            <Button variant="outline" size="sm" onClick={goToNext}>
              {t('Skip')}<i className="fas fa-forward" />
            </Button>
          )}
        </div>
      </header>

      {justSubmitted && (
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl border border-green-200 bg-green-50 text-green-800">
          <i className="fas fa-check-circle text-xl" />
          <span className="flex-1 font-semibold">{t('Review submitted. Thank you!')}</span>
          {nextId ? (
            <Button size="sm" onClick={goToNext}>{t('Next review')}<i className="fas fa-arrow-right" /></Button>
          ) : (
            <Link to={`/${event.key}/reviews`} className="text-sm font-semibold hover:underline">
              {t('Return to review list')}
            </Link>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <section className="bg-white rounded-2xl border border-border shadow-sm lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] flex flex-col">
          <div className="px-6 py-4 border-b border-border">
            <h2 className="font-heading text-base font-bold text-foreground">{t('Application')}</h2>
          </div>
          <div className="p-6 overflow-y-auto">
            <ResponseAnswers form={data.application_form} answers={data.application_response.answers} language={language} />
          </div>
        </section>

        <section className="bg-white rounded-2xl border border-border shadow-sm">
          <FormRenderer
            key={data.review_response.id}
            form={data.review_form}
            response={data.review_response}
            linkedResponse={data.application_response}
            language={language}
            onSave={save}
            onSubmit={submit}
            onAnswersChange={setAnswers}
            showConfirmation={false}
            readOnly={!data.review_form.is_open}
            autoSaveInterval={isSubmitted ? 0 : 30000}
          />
        </section>
      </div>

      <FlagModal visible={flagVisible} onClose={() => setFlagVisible(false)}
                 eventId={event.id} applicantUserId={data.applicant_user_id} t={t} />
    </div>
  );
}

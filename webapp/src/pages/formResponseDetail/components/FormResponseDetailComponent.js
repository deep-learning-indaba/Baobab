import React, { Component } from "react";
import { withTranslation } from "react-i18next";
import { formResponseService } from "../../../services/formResponse";
import { formServices } from "../../../services/form/form.service";
import { getDownloadURL } from "../../../utils/files";

class FormResponseDetailComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      response: null,
      form: null,
      loading: true,
      error: null
    };
  }

  componentDidMount() {
    this.loadData();
  }

  componentDidUpdate(prevProps) {
    const prevFormId = prevProps.formId || (prevProps.match && prevProps.match.params.formId);
    const prevResponseId = prevProps.responseId || (prevProps.match && prevProps.match.params.responseId);
    const formId = this.props.formId || (this.props.match && this.props.match.params.formId);
    const responseId = this.props.responseId || (this.props.match && this.props.match.params.responseId);
    if (prevFormId !== formId || prevResponseId !== responseId) {
      this.loadData();
    }
  }

  getFormId() {
    return this.props.formId || (this.props.match && this.props.match.params.formId);
  }

  getResponseId() {
    return this.props.responseId || (this.props.match && this.props.match.params.responseId);
  }

  loadData = async () => {
    this.setState({ loading: true, error: null });
    const formId = this.getFormId();
    const responseId = this.getResponseId();
    const eventId = this.props.event ? this.props.event.id : null;

    if (!eventId || !formId || !responseId) {
      this.setState({ loading: false, error: this.props.t("Missing required parameters") });
      return;
    }

    const [formResult, responseResult] = await Promise.all([
      formServices.getFormStructure(formId, this.props.language || 'en'),
      formResponseService.getResponseDetailAdmin(eventId, formId, responseId)
    ]);

    if (formResult.error || responseResult.error) {
      this.setState({ loading: false, error: formResult.error || responseResult.error });
      return;
    }

    this.setState({
      form: formResult.form,
      response: responseResult.response,
      loading: false
    }, () => {
      if (this.props.onResponseLoad) {
        this.props.onResponseLoad(responseResult.response, formResult.form, this.loadData);
      }
    });
  };

  handleBack = () => {
    this.props.history.goBack();
  };

  getQuestionText(question, lang) {
    if (!question) return '';
    const headline = question.headline;
    if (!headline) return '';
    if (typeof headline === 'string') return headline;
    return headline[lang] || headline['en'] || Object.values(headline)[0] || '';
  }

  getQuestionOptions(question, lang) {
    if (!question || !question.options) return [];
    const opts = question.options;
    if (Array.isArray(opts)) return opts;
    return opts[lang] || opts['en'] || Object.values(opts)[0] || [];
  }

  renderAnswerValue(answer, question) {
    const { t } = this.props;
    if (!answer || answer.value === null || answer.value === undefined || answer.value === '') {
      return <span className="text-muted-foreground italic">{t('No answer provided.')}</span>;
    }

    const type = question ? question.type : null;
    const value = answer.value;
    const lang = this.props.language || 'en';

    if (type === 'file') {
      return (
        <a href={getDownloadURL(value)} target="_blank" rel="noopener noreferrer"
           className="text-primary hover:underline">
          {t('Uploaded File')}
        </a>
      );
    }

    if (type === 'multi-file') {
      try {
        const files = JSON.parse(value);
        if (Array.isArray(files) && files.length > 0) {
          return (
            <div className="space-y-1">
              {files.map(f => (
                <div key={f.name}>
                  <a href={getDownloadURL(JSON.stringify(f))} target="_blank" rel="noopener noreferrer"
                     className="text-primary hover:underline">{f.name}</a>
                </div>
              ))}
            </div>
          );
        }
      } catch (_) {}
      return <span className="text-muted-foreground italic">{t('No files uploaded')}</span>;
    }

    if (type === 'dropdown' || type === 'multi-choice') {
      const options = this.getQuestionOptions(question, lang);
      const match = options.find(o => o.value === value);
      return <span>{match ? match.label : value}</span>;
    }

    if (type === 'checkboxes') {
      try {
        const selected = JSON.parse(value);
        if (Array.isArray(selected)) {
          const options = this.getQuestionOptions(question, lang);
          const labels = selected.map(v => {
            const opt = options.find(o => o.value === v);
            return opt ? opt.label : v;
          });
          return <span>{labels.join(', ')}</span>;
        }
      } catch (_) {}
    }

    if (type === 'single-checkbox') {
      return <span>{value === 'true' || value === true ? t('Yes') : t('No')}</span>;
    }

    return <span className="whitespace-pre-wrap">{value}</span>;
  }

  buildQuestionMap() {
    const map = {};
    if (!this.state.form) return map;
    for (const section of this.state.form.sections || []) {
      for (const q of section.questions || []) {
        map[q.id] = q;
      }
    }
    return map;
  }

  renderFormContent() {
    const { t } = this.props;
    const { form, response } = this.state;
    if (!form || !response) return null;

    const lang = this.props.language || 'en';
    const answersByQuestionId = {};
    for (const a of response.answers || []) {
      answersByQuestionId[a.question_id] = a;
    }

    return (form.sections || []).map(section => {
      const sectionName = section.name
        ? (typeof section.name === 'string' ? section.name : section.name[lang] || section.name['en'] || '')
        : '';
      const visibleQuestions = (section.questions || []).filter(q => q.type !== 'information');
      if (visibleQuestions.length === 0) return null;

      return (
        <div key={section.id} className="space-y-4">
          {sectionName && (
            <h3 className="text-base font-bold text-foreground border-b border-border pb-2">{sectionName}</h3>
          )}
          {visibleQuestions.map(q => {
            const questionText = this.getQuestionText(q, lang);
            const answer = answersByQuestionId[q.id];
            return (
              <div key={q.id} className="space-y-1">
                <p className="text-sm font-semibold text-foreground/90">{questionText}</p>
                <div className="text-sm text-foreground pl-2">
                  {this.renderAnswerValue(answer, q)}
                </div>
              </div>
            );
          })}
        </div>
      );
    });
  }

  render() {
    const { t, renderAdminContent } = this.props;
    const { response, loading, error } = this.state;

    if (loading) {
      return (
        <div className="flex justify-center items-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="max-w-3xl mx-auto pt-8 px-4">
          <div className="bg-error/10 text-error border border-error/20 p-6 rounded-xl text-sm">
            <p className="font-semibold mb-2">{t('Error')}</p>
            <p>{error}</p>
            <button className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                    onClick={this.handleBack}>
              ← {t('Go Back')}
            </button>
          </div>
        </div>
      );
    }

    if (!response) {
      return (
        <div className="max-w-3xl mx-auto pt-8 px-4">
          <div className="bg-amber-50 text-amber-700 border border-amber-200 p-6 rounded-xl text-sm">
            <p className="font-semibold">{t('Response Not Found')}</p>
            <button className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                    onClick={this.handleBack}>
              ← {t('Go Back')}
            </button>
          </div>
        </div>
      );
    }

    const formContent = (
      <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={this.handleBack}
            className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
          >
            ← {t('Back')}
          </button>
          {response.user && (
            <h1 className="font-heading text-2xl font-bold text-foreground">
              {response.user.user_title} {response.user.firstname} {response.user.lastname}
            </h1>
          )}
        </div>

        <div className="flex flex-wrap gap-2 text-sm">
          <span className={`inline-flex items-center px-3 py-1 rounded-full font-semibold text-xs border ${
            response.is_withdrawn ? 'bg-error/10 text-error border-error/20' :
            response.is_submitted ? 'bg-green-50 text-green-700 border-green-200' :
            'bg-amber-50 text-amber-700 border-amber-200'
          }`}>
            {response.is_withdrawn ? t('Withdrawn') : response.is_submitted ? t('Submitted') : t('Draft')}
          </span>
          <span className="text-muted-foreground">{t('Language')}: {(response.language || 'en').toUpperCase()}</span>
          {response.user && (
            <span className="text-muted-foreground">{response.user.email}</span>
          )}
        </div>

        <div className="space-y-6">
          {this.renderFormContent()}
        </div>
      </div>
    );

    if (renderAdminContent) {
      return (
        <div className="w-full max-w-6xl mx-auto pt-6 px-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">{formContent}</div>
            <div className="space-y-4">
              {renderAdminContent(response, this.state.form, this.loadData)}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="w-full max-w-3xl mx-auto pt-6 px-4">
        {formContent}
      </div>
    );
  }
}

export default withTranslation()(FormResponseDetailComponent);

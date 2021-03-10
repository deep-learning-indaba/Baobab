import React, { useState, forwardRef, useEffect, useCallback, useMemo } from 'react';
import { default as ReactSelect } from "react-select";
import {
  option, Modal, handleMove, Dependency, dependencyChange,
  Validation, validationText as vText, langObject, rows
} from './util';

const Question = forwardRef(({
    inputs, t, questions, sectionId, setSections,
    lang, section, sections, optionz, langs,
    setApplytransition, questionIndex, setQuestionAnimation,
    handleDrag, handleDrop, showingQuestions, setDisableSaveBtn
  }, ref) => {
  const [isModelVisible, setIsModelVisible] = useState(false);
  const [isValidateOn, setIsvalidateOn] = useState(false);
  const [isKeyOn, setIsKeyOn] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const opts = inputs.options[lang];
  const type = inputs.type;
  const max_num_referral = inputs.options[lang] && inputs.options[lang].max_num_referral;
  const min_num_referral = inputs.options[lang] && inputs.options[lang].min_num_referral;
  const validation_regex = inputs.validation_regex[lang];
  const key = inputs.key;
  let maxSurrogateId = 1;
  sections.forEach(s => {
    if (s.backendId > maxSurrogateId) {
      maxSurrogateId = s.backendId;
    }
    s.questions.forEach(q => {
      if (q.backendId > maxSurrogateId) {
        maxSurrogateId = q.backendId
      }
      if (q.surrogate_id > maxSurrogateId) {
        maxSurrogateId = q.surrogate_id
      }
    })
  })

  useEffect(() => {
    if ((type === 'reference') && (!max_num_referral || !min_num_referral)) {
      setErrorMessage('Max and min Rererrals are required');
      // isSaveDisabled = true;
    }
    else if (max_num_referral < min_num_referral) {
      setErrorMessage('Max referral value must be greater than Min');
      // isSaveDisabled = true;
    }
    else if ((type === 'multi-choice'|| type === 'multi-checkbox')
      && opts && !opts.length) {
      setErrorMessage('At least one option is required');
      // isSaveDisabled = true;
    } else {
      setErrorMessage('');
    }
  }, [opts, max_num_referral, min_num_referral]);

  useEffect(() => {
    if (errorMessage) {
      setDisableSaveBtn(true)
    } else {
      setDisableSaveBtn(false)
    }
  }, [errorMessage])

  useEffect(() => {
    if (validation_regex) {
      setIsvalidateOn(true)
    }
  }, [validation_regex]);

  useEffect(() => {
    if (key) {
      setIsKeyOn(true)
    }
  }, [key])

  const handleChange = (prop) => (e) => {
    const target = inputs[prop];
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            let regex = q.validation_regex[lang];
            if (prop === 'min' || prop === 'max') {
              if (!regex || !regex.split('{')[1]) {
                regex = `^\s*(\S+(\s+|$)){0,0}$`
              }
            }
            const maxMin = (prop === 'min' || prop === 'max')
              && regex
              && regex.split('{')[1].split(',');

            if (prop === 'min') {
              const validation = q.validation_regex;
              const validationText = q.validation_text;
              let max = maxMin ? parseInt(maxMin[1].split('}')[0]) : '';
              const min = e.target.value;

              if (min >= max) {
                max = '';
              }
              q = {
                ...q,
                validation_regex: {
                  ...validation,
                  [lang]: `^\s*(\S+(\s+|$)){${min},${max}}$`
                }
              }
              q = {
                ...q,
                validation_text: {
                  ...validationText,
                  [lang]: vText(min, max, t)
                }
              }
            }
            if (prop === 'max') {
              const validation = q.validation_regex;
              const validationText = q.validation_text;
              const min = maxMin ? parseInt(maxMin[0]) : 0;
              let max = e.target.value;
              q = {
                ...q,
                validation_regex: {
                  ...validation,
                  [lang]: `^\s*(\S+(\s+|$)){${min},${max}}$`
                }
              }
              q = {
                ...q,
                validation_text: {
                  ...validationText,
                  [lang]: vText(min, max, t)
                }
              }
            } else {
              if (prop === 'key') {
                q = {...q, [prop]: e.target.value}
              } else {
                q = {...q, [prop]: {...target, [lang]: e.target.value}}
              }
            }
          }
          return q
        })}
      }
      return s
    });
    setApplytransition(false)
    setQuestionAnimation(false)
    setSections(updatedSections)
  }

  const handleTypeChange = (e) => {
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            if (e.value === 'reference') {
              q = {
                ...q,
                options: {
                  min_num_referral: null,
                  max_num_referral: null
                }
              }
            } else {

              q = {...q, options: langObject(langs, [])}
            }
            q = {...q, type: e.value}
          }
          return q
        })}
      }
      return s
    });
    setSections(updatedSections)
  }

  const handleCheckChanged = (e) => {
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            q = {...q, required: e.target.checked}
          }
          return q
        })}
      }
      return s
    });
    setSections(updatedSections);
  }

  const handleAddOption = () => {
    const opt = inputs.options;
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            q = {...q, options: {...opt, [lang]: [{
              id: `${Math.random()}`,
              value: inputs.value[lang],
              label: inputs.label[lang],
            }, ...opt[lang]]}}
          }
          return q
        })}
      }
      return s
    });
    if (!inputs.value[lang] || !inputs.label[lang]) {
      setErrorMessage('Label or Value cannot be empty');
    } else {
      setSections(updatedSections);
    }
  }

  const resetInputs = () => {
    const { value, label } = inputs;
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            q = {...q, value: {...value, [lang]: ''}};
            q = {...q, label: {...label, [lang]: ''}}
          }
          return q
        })}
      }
      return s
    });
    setSections(updatedSections);
  }

  const handleDeleteOption = (id, e) => {
    const newOptions = inputs.options[lang].filter(o => o.id !== id);
    const opt = inputs.options;
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            q = {...q, options: {...opt, [lang]: newOptions}}
          }
          return q
        })}
      }
      return s
    });
    setSections(updatedSections);
    setQuestionAnimation(false);
    setApplytransition(false);
  }

  const handleOkDelete = () => {
    const questionsWithNoDependency = questions.map(q => {
      if ((q.depends_on_question_id === inputs.backendId)
        || (q.depends_on_question_id === inputs.surrogate_id)) {
        q = {...q, depends_on_question_id: 0}
      }
      return q
    });
    const sectionsWithNoDependency = sections.map(s => {
      if (s.id === sectionId) {
        if ((s.depends_on_question_id === inputs.backendId)
          || (s.depends_on_question_id === inputs.surrogate_id)) {
          s = {...s, depends_on_question_id: 0}
        }
        s = {...s, questions: questionsWithNoDependency}
      }
      return s;
    });
    const newQuestions = questionsWithNoDependency.filter(q => q.id !== inputs.id);
    const orderedQuestions = newQuestions.map((q, i) => ({...q, order: i + 1}));
    const updatedSections = sectionsWithNoDependency.map(s => {
      if (s.id === sectionId) {
        s = {...s, questions: orderedQuestions}
      }
      return s;
    });
    setSections(updatedSections);
    setQuestionAnimation(false);
  }

  const handleConfirm = () => {
    setIsModelVisible(!isModelVisible);
    setApplytransition(false);
  }

  const handleMoveQuestionUp = () => {
    handleMove({
      elements: questions,
      index: questionIndex,
      section: section,
      setAnimation: setQuestionAnimation,
      sections,
      setSection: setSections,
      id: inputs.id,
      isUp: true
    });
  }

  const handleMoveQuestionDown = () => {
    handleMove({
      elements: questions,
      index: questionIndex,
      section: section,
      setAnimation: setQuestionAnimation,
      sections,
      id: inputs.id,
      setSection: setSections,
    });
  }

  const handleDropOver = (e) => {
    e.preventDefault();
  }

  const handlequestionDependency = (e) => {
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            q = {...q, depends_on_question_id: parseInt(e.value)}
          }
          return q
        })}
      }
      return s
    });
    setSections(updatedSections);
  }

  const handleDependencyChange = (prop) => (e) => {
    dependencyChange({
      prop:prop,
      e:e,
      sections:sections,
      inputs:inputs,
      setSection:setSections,
      question: true,
      sectionId:sectionId,
      lang: lang
    })
  }

  const handleValidation = () => {
    setIsvalidateOn(!isValidateOn);
  }

  const handleKey = () => {
    setIsKeyOn(!isKeyOn);
  }

  const handlereferralsChange = (prop) => (e) => {
    let min;
    let max;
    if (prop === 'min') {
      max = inputs.options[lang]
        && inputs.options[lang].max_num_referral;
      min = e.target.value;
    }
    if (prop === 'max') {
      min = inputs.options[lang]
        && inputs.options[lang].min_num_referral;
      max = e.target.value;
    }
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            const options = q.options;
            q = {...q, options: {...options, [lang]: {
              min_num_referral: min,
              max_num_referral: max
            }}}
          }
          return q
        })}
      }
      return s
    });
    setSections(updatedSections);
  }

  const handlereExtensionChange = (e) => {
    const opt = inputs.options;
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            const ext = e.target.value.split(',').map(e => e.trim())
            q = {...q, options: {...opt, [lang]: { accept: ext }}}
          }
          return q
        })}
      }
      return s
    });
    setSections(updatedSections);
  }

  const handleDuplicate = () => {
    const duplicate = {
      id: `${Math.random()}`,
      surrogate_id: maxSurrogateId + 1,
      depends_on_question_id: inputs.depends_on_question_id,
      headline: inputs.headline,
      description: inputs.description,
      required: inputs.required,
      key: inputs.key,
      options: inputs.options,
      order: inputs.order,
      placeholder: inputs.placeholder,
      show_for_values: inputs.show_for_values,
      type: inputs.type,
      validation_regex: inputs.validation_regex,
      validation_text: inputs.validation_text
    };
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        const index = inputs.order;
        const questions = [...s.questions];
        questions.splice(index, 0, duplicate);
        s = {...section, questions: questions.map((q, i) => {
          q = {...q, order: i + 1}
          return q
        }
        )}
      }
      return s
    });
    setSections(updatedSections);
    setQuestionAnimation(false);
    setApplytransition(false);
  }

  const options = [
    option({
      value: 'short-text',
      label: 'Short Text',
      faClass: 'fa fa-align-left fa-xs fa-color',
      t
    }),
    option({
      value: 'long-text',
      label: 'Long Text',
      faClass: 'fas fa-align-justify fa-color',
      t
    }),
    option({
      value: 'markdown',
      label: 'Markdown',
      faClass: 'fab fa-markdown fa-color',
      t
    }),
    option({
      value: 'single-choice',
      label: 'Single Choice',
      faClass: 'fas fa-check-circle fa-color',
      t
    }),
    option({
      value: 'multi-choice',
      label: 'Multi Choice',
      faClass: 'far fa-caret-square-down fa-color',
      t
    }),
    option({
      value: 'multi-checkbox',
      label: 'Multi Checkbox',
      faClass: 'fas fa-check-square fa-color',
      t
    }),
    option({
      value: 'file',
      label: 'File',
      faClass: 'fas fa-cloud-upload-alt fa-color',
      t
    }),
    option({
      value: 'date',
      label: 'Date',
      faClass: 'fas fa-calendar-alt fa-color',
      t
    }),
    option({
      value: 'reference',
      label: 'Reference',
      faClass: 'fas fa-user fa-color',
      t
    }),
    option({
      value: 'multi-file',
      label: 'Multi File',
      faClass: 'fas fa-cloud fa-color',
      t
    }),
  ];

  const validationOptions = [
    option({
      value: 'friendly-mode',
      label: 'Word Limit',
      t
    }),
    option({
      value: 'advanced-mode',
      label: 'Advanced Mode',
      t
    }),
  ]

  const withPlaceHolder = ['short-text', 'multi-choice', 'long-text'];
  const withOptions = ['multi-choice', 'multi-checkbox'];
  const withReferals = ['reference'];
  const withExtention = ['file', 'multi-file'];
  const withRegex = ['long-text', 'short-text', 'markdown'];
  const dependencyOptions = optionz.filter(e => e.order < inputs.order);
  let style = inputs.required
    ? {display: 'block', boxShadow: '0px 0.3em 5px 0px #e8e6e6'}
    : {display: 'block'};
  if (!showingQuestions) {
    style = {display: 'none'}
  }

  const dependentQuestion = section.questions
    .find(e => (e.backendId === inputs.depends_on_question_id)
      || (e.surrogateId === inputs.depends_on_question_id));

  return (
    <>
      <div
        className="section-wrapper"
        key={inputs.id}
        id={inputs.id}
        ref={ref}
        draggable={true}
        onDragOver={handleDropOver}
        onDragStart={handleDrag}
        onDrop={handleDrop}
        style={style}
      >
        <div className="headline-description">
          <div className="question-header">
            <span className="key-wrapper">
            {!inputs.headline[lang] && (
              <span className='tooltiptext-error'>{t('Headline is Required')}</span>
            )}
              <input
                type="text"
                name="headline"
                value={inputs.headline[lang]}
                onChange={handleChange('headline')}
                placeholder={t('Headline')}
                className="section-inputs question-title"
              />
              <span className="tooltiptext">{t('Headline')}</span>
            </span>
            {!type && (
              <span className='tooltiptext-error'>{t('Type is Required')}</span>
            )}
            <ReactSelect
              options={options}
              placeholder={t('Choose type')}
              onChange={e => handleTypeChange(e)}
              defaultValue={inputs.type || null}
              value={options.find(o => o.value === inputs.type)}
              className='select-form'
              styles={{
                control: (base, state) => ({
                  ...base,
                  boxShadow: "none",
                  border: state.isFocused && "none",
                  transition: state.isFocused && 'color,background-color 1.5s ease-out',
                  background: state.isFocused && 'lightgray',
                  color: '#fff'
                }),
                option: (base, state) => ({
                   ...base,
                   backgroundColor: state.isFocused && "lightgray",
                   color: state.isFocused && "#fff"
                })
              }}
              menuPlacement="auto"
            />
            <div className='move-btns-wrapper'>
              <button
                className="move-btn"
                data-title={t("Move up")}
                onClick={handleMoveQuestionUp}
              >
                <i className="fas fa-chevron-up fa-move"></i>
              </button>
              <button
                className="move-btn"
                data-title={t("Move down")}
                onClick={handleMoveQuestionDown}
              >
                <i className="fas fa-chevron-down fa-move"></i>
              </button>
            </div>
          </div>
          <div className="label-input-wrapper">
            <label htmlFor="section-desc" className="form-label">{t('Description')}</label>
            <textarea
              name='section-desc'
              placeholder={t('Description')}
              onChange={handleChange('description')}
              className="section-inputs section-desc section-key"
              rows={rows(inputs.description[lang])}
              value={inputs.description[lang] || ''}
            />
          </div>
          {isKeyOn && (
            <div className="label-input-wrapper">
              <label htmlFor="section-desc" className="form-label">{t('Key')}</label>
              <input
                name="section-desc"
                type="text"
                value={inputs.key}
                placeholder={t('Key')}
                onChange={handleChange('key')}
                className="section-inputs section-desc section-key"
                />
            </div>
          )}
          {withPlaceHolder.includes(inputs.type) && (
            <div className="label-input-wrapper">
              <label htmlFor="question-headline" className="form-label">{t('Placeholder')}</label>
              <input
                name="question-headline"
                type="text"
                value={inputs.placeholder[lang] || ''}
                placeholder={t('Placeholder')}
                onChange={handleChange('placeholder')}
                className="question-inputs question-headline"
                />
            </div>
          )}
          {withOptions.includes(inputs.type) && (
            <div className="options">
              <table
                className='options-table'
              >
                <tbody className='options-row'>
                  <tr className='options-row'>
                    <td className='options-row'>
                      <input
                        type='text'
                        placeholder={t('Value')}
                        onChange={handleChange('value')}
                        value={inputs.value && inputs.value[lang]}
                        className='option-inputs'
                      />
                    </td>
                    <td className='options-row'>
                      <input
                        type='text'
                        placeholder={t('Label')}
                        value={inputs.label && inputs.label[lang]}
                        onChange={handleChange('label')}
                        className='option-inputs'
                      />
                    </td>
                    <td className='options-row'>
                      <i
                        className="fas fa-plus-circle  fa-lg fa-table-btns add-row"
                        data-title={t('Add')}
                        onMouseDown={handleAddOption}
                        onMouseUp={resetInputs}
                      ></i>
                    </td>
                  </tr>
                </tbody>
                <tbody className='options-row'>
                  {inputs.options[lang].map((option, i) => (
                    <tr key={i} className='options-row'>
                      <td className='options-row'>
                        <input
                          type='text'
                          value={option.value}
                          className='option-inputs'
                          disabled
                        />
                      </td>
                      <td className='options-row'>
                        <input
                          type='text'
                          value={option.label}
                          className='option-inputs'
                          disabled
                        />
                      </td>
                      <td className='options-row'>
                        <i
                          data-title={t('Delete')}
                          className="fas fa-minus-circle fa-lg fa-table-btns delete-row"
                          onClick={e => handleDeleteOption(option.id, e)}
                        ></i>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <span className='error-label'>{t(errorMessage)}</span>
          </div>
          )}
          {withReferals.includes(inputs.type) && (
            <div className='referals-wrapper'>
              <div className="min-wrapper">
                <label
                  htmlFor="min-ref"
                  className="validation-label referalls-label"
                  >
                  {t('Minimum Number of Referrals')}
                  </label>
                <input
                  type='number'
                  min={0}
                  placeholder={t('Enter Minimum Number of Referrals')}
                  className='referals-input'
                  value={inputs.options[lang]
                    && inputs.options[lang].min_num_referral}
                  onChange={handlereferralsChange('min')}
                />
              </div>
              <div className="min-wrapper">
                <label
                  htmlFor="max-ref"
                  className="validation-label referalls-label"
                  >
                    {t('Maximum Number of Referrals')}
                </label>
                <input
                  type='number'
                  min={0}
                  placeholder={t('Enter Maximum Number of Referrals')}
                  className='referals-input'
                  onChange={handlereferralsChange('max')}
                  value={inputs.options[lang]
                    && inputs.options[lang].max_num_referral}
                />
              </div>
              <div className='error-label'>{t(errorMessage)}</div>
            </div>
          )}
          {withExtention.includes(inputs.type) && (
            <div className='extensions-wrapper'>
              <label
                htmlFor="extensions"
                className="extension-label"
              >
                {t('Extensions (E.g .csv,.xls)')}
              </label>
              <input
                name="extensions"
                id="extensions"
                type='text'
                placeholder={
                  t('Please enter a list of file extensions, each starting with a period and separated with commas. E.g .csv,.xls')}
                className='question-inputs question-headline'
                value={(inputs.options[lang] && inputs.options[lang].accept
                  && inputs.options[lang].accept.join(',')) || ''}
                onChange={handlereExtensionChange}
               />
            </div>
          )}
          {isValidateOn
            && <Validation
                t={t}
                options={validationOptions}
                inputs={inputs}
                lang={lang}
                handleChange={handleChange}
              />
          }
          <Dependency
            options={dependencyOptions}
            handlequestionDependency={handlequestionDependency}
            handleDependencyChange={handleDependencyChange}
            dependentQuestion={dependentQuestion}
            inputs={inputs}
            lang={lang}
            t={t}
            />
          <div className="action-btns">
            <div className="question-footer">
              <button
                className="delete-qstion duplicate-qstion"
                data-title="Duplicate"
                onClick={handleDuplicate}
              >
                <i className="far fa-copy fa-md fa-color"></i>
              </button>
              <button
                className="delete-qstion delete-btn"
                data-title={t('Delete')}
                onClick={handleConfirm}
              >
                <i
                  className="far fa-trash-alt fa-md fa-color"
                  ></i>
              </button>
              <div className='require-chckbox'>
                <input
                  type='checkbox'
                  id={`required_${inputs.id}`}
                  checked={inputs.required}
                  onChange={e => handleCheckChanged(e)}
                  className='require-check'
                />
                <label htmlFor={`required_${inputs.id}`}>{t('Required')}</label>
              </div>
            </div>
          </div>
          <div
            id="toggleTitle"
            className="title-desc-toggle toggle-questions"
            role="button"
            data-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
          >
            <i
              className='fa fa-ellipsis-v fa-lg fa-dropdown fa-question-toogle'
              ></i>
          </div>
          <div className="dropdown-menu" aria-labelledby="toggleTitle">
            <button
              className="dropdown-item delete-section"
              onClick={handleValidation}
              disabled={!withRegex.includes(inputs.type)}
              >
              <span className="check-icon">
                {isValidateOn
                  && <i className="fas fa-check fa-validation"></i>
                }
              </span>
                {t("Validation")}
            </button>
            <button
              className="dropdown-item delete-section"
              onClick={handleKey}
              >
              <span className="check-icon">
                {isKeyOn
                  && <i className="fas fa-check fa-validation"></i>
                }
              </span>
                {t("Key")}
            </button>
          </div>
        </div>
        {isModelVisible && (
          <Modal
            t={t}
            element='question'
            handleOkDelete={handleOkDelete}
            handleConfirm={handleConfirm}
            sections={sections}
            questions={questions}
            inputs={inputs}
          />
          )}
      </div>
    </>
  )
})

export default Question;

import React, { useState, forwardRef } from 'react';
import { default as ReactSelect } from "react-select";
import {
  option, Modal, handleMove
} from './util';

const Question = forwardRef(({
    inputs, t, questions, sectionId, setSections,
    lang, section, sections,
    setApplytransition, questionIndex, setQuestionAnimation,
    handleDrag, handleDrop, showingQuestions
}, ref) => {
  const [isModelVisible, setIsModelVisible] = useState(false);

  const handleChange = (prop) => (e) => {
    const target = inputs[prop];
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            q = {...q, [prop]: {...target, [lang]: e.target.value}}
          }
          return q
        })}
      }
      return s
    });
    setSections(updatedSections)
  }
  const handleTypeChange = (e) => {
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            q = {...q, type: e}
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
    setSections(updatedSections);
  }

  const resetInputs = () => {
    const { value, label } = inputs;
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...section, questions: s.questions.map(q => {
          if (q.id === inputs.id) {
            q = {...q, value: {...value, [lang]: '',
              label: {...label, [lang]: ''}}}
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
  }

  const handleOkDelete = () => {
    const newQuestions = questions.filter(q => q.id !== inputs.id);
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...s, questions: newQuestions}
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

  const withPlaceHolder = ['short-text', 'multi-choice', 'long-text', 'markdown'];
  const withOptions = ['multi-choice', 'multi-checkbox'];
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
        style={showingQuestions ? {display: 'block'} : {display: 'none'}}
      >
        <div className="headline-description">
          <div className="question-header">
            <input
              type="text"
              name="headline"
              value={inputs.headline[lang]}
              onChange={handleChange('headline')}
              placeholder={t('Headline')}
              className="section-inputs question-title"
            />
            <ReactSelect
              options={options}
              placeholder={t('Choose type')}
              onChange={e => handleTypeChange(e)}
              defaultValue={inputs.type || null}
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
                <i class="fas fa-chevron-up fa-move"></i>
              </button>
              <button
                className="move-btn"
                data-title={t("Move down")}
                onClick={handleMoveQuestionDown}
              >
                <i class="fas fa-chevron-down fa-move"></i>
              </button>
            </div>
          </div>
          {withPlaceHolder.includes(inputs.type && inputs.type.value) && (
            <input
              name="question-headline"
              type="text"
              value={inputs.placeholder[lang]}
              placeholder={t('Placeholder')}
              onChange={handleChange('placeholder')}
              className="question-inputs question-headline"
            />
          )}
          {withOptions.includes(inputs.type && inputs.type.value) && (
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
                        value={inputs.value[lang]}
                        className='option-inputs'
                      />
                    </td>
                    <td className='options-row'>
                      <input
                        type='text'
                        placeholder={t('Label')}
                        value={inputs.label[lang]}
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
          </div>
          )}
          
          <div className="action-btns">
            <div className="question-footer">
              <button
                className="delete-qstion duplicate-qstion"
                data-title="Duplicate"
              >
                <i className="far fa-copy fa-md fa-color"></i>
              </button>
              <button
                className="delete-qstion delete-btn"
                data-title={t('Delete')}
                onClick={handleConfirm}
              >
                <i className="far fa-trash-alt fa-md fa-color"></i>
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
        </div>
        {isModelVisible && (
            <Modal
              t={t}
              element='question'
              handleOkDelete={handleOkDelete}
              handleConfirm={handleConfirm}
            />
          )}
      </div>
    </>
  )
})

export default Question;

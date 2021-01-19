import React, { useState } from 'react';
import { default as ReactSelect } from "react-select";

const Section = ({
    inputs, t, questions, setQuestions, num,
    setSection, sections
}) => {
  const [input, setInput] = useState({
    headline: inputs.headline,
    placeholder: inputs.placeholder,
    id: inputs.id,
    order: inputs.order,
    type: inputs.type,
    options: inputs.options,
    value: inputs.value,
    label: inputs.label,
    required: inputs.required
  });

  const handleChange = (prop) => (e) => {
    setInput({...input, [prop]: e.target.value});
  }
  const handleTypeChange = (e) => {
    setInput({...input, type: e});
  }
  const handleCheckChanged = (e) => {
    setInput({...input, 'required': e.target.checked});
  }

  const handleAddOption = () => {
    setInput({...input, options: [{
      id: `${Math.random()}`,
      value: input.value,
      label: input.label,
    }, ...input.options]});
  }
  const resetInputs = () => {
    setInput({...input, value: '', label: ''});
  }
  const handleDeleteOption = (id, e) => {
    const newOptions = input.options.filter(e => e.id !== id);
    setInput({...input, options: [...newOptions]})
  }

  const updateQuestions = () => { // Update questions in the sections form when question loses focus
    questions[num-1] = input;
    setQuestions([...questions]);
  }

  const option = props => {
    const { value } = props;
    const label = <div>
      <div className='dropdown-text'>
        <i className={props.faClass}></i>
      </div>
      {t(props.label)}
    </div>
    return {
      label,
      value
    }
  }

  const options = [
    option({
      value: 'short-text',
      label: 'Short Text',
      faClass: 'fa fa-align-left fa-xs fa-color'
    }),
    option({
      value: 'long-text',
      label: 'Long Text',
      faClass: 'fas fa-align-justify fa-color'
    }),
    option({
      value: 'markdown',
      label: 'Markdown',
      faClass: 'fab fa-markdown fa-color'
    }),
    option({
      value: 'single-choice',
      label: 'Single Choice',
      faClass: 'fas fa-check-circle fa-color'
    }),
    option({
      value: 'multi-choice',
      label: 'Multi Choice',
      faClass: 'far fa-caret-square-down fa-color'
    }),
    option({
      value: 'multi-checkbox',
      label: 'Multi Checkbox',
      faClass: 'fas fa-check-square fa-color'
    }),
    option({
      value: 'file',
      label: 'File',
      faClass: 'fas fa-cloud-upload-alt fa-color'
    }),
    option({
      value: 'date',
      label: 'Date',
      faClass: 'fas fa-calendar-alt fa-color'
    }),
    option({
      value: 'reference',
      label: 'Reference',
      faClass: 'fas fa-user fa-color'
    }),
    option({
      value: 'multi-file',
      label: 'Multi File',
      faClass: 'fas fa-cloud fa-color'
    }),
  ];
  const withPlaceHolder = ['short-text', 'multi-choice', 'long-text', 'markdown'];
  const withOptions = ['multi-choice', 'multi-checkbox'];
  return (
    <>
      <div
        className="section-wrapper"
        onBlur={updateQuestions}
      >
        <div className="headline-description">
          <div className="question-header">
            <input
              type="text"
              name="headline"
              value={input.headline}
              onChange={handleChange('headline')}
              className="section-inputs question-title"
              onBlur={updateQuestions}
            />
            <ReactSelect
              id={input.id}
              options={options}
              placeholder={t('Choose type')}
              onChange={e => handleTypeChange(e)}
              defaultValue={input.type || null}
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
          </div>
          {withPlaceHolder.includes(input.type && input.type.value) && (
            <input
            name="section-desc"
            type="text"
            value={input.placeholder}
            placeholder={t('Place holder')}
            onChange={handleChange('placeholder')}
            className="section-inputs section-desc"
            onFocus={updateQuestions}
            onBlur={updateQuestions}
          />
          )}
          {withOptions.includes(input.type && input.type.value) && (
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
                        value={input.value}
                        onChange={handleChange('value')}
                        className='option-inputs'
                      />
                    </td>
                    <td className='options-row'>
                      <input
                        type='text'
                        placeholder='Label'
                        value={input.label}
                        onChange={handleChange('label')}
                        className='option-inputs'
                      />
                    </td>
                    <td className='options-row'>
                      <i
                        className="fas fa-plus-circle  fa-lg fa-table-btns add-row"
                        data-title='Add'
                        onMouseDown={handleAddOption}
                        onMouseUp={resetInputs}
                      ></i>
                    </td>
                  </tr>
                </tbody>
                <tbody className='options-row'>
                  {input.options.map((option, i) => (
                    <tr key={i} className='options-row'>
                      <td className='options-row'>
                        <input
                          type='text'
                          value={option.value}
                          className='option-inputs'
                          // disabled
                        />
                      </td>
                      <td className='options-row'>
                        <input
                          type='text'
                          value={option.label}
                          className='option-inputs'
                          // disabled
                        />
                      </td>
                      <td className='options-row'>
                        <i
                          data-title='Delete'
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
              <button className="delete-qstion duplicate-qstion" data-title="Duplicate">
                <i className="far fa-copy fa-md fa-color"></i>
              </button>
              <button className="delete-qstion delete-btn" data-title="Delete">
                <i className="far fa-trash-alt fa-md fa-color"></i>
              </button>
              <div className='require-chckbox'>
                <input
                  type='checkbox'
                  id={`required_${input.id}`}
                  checked={input.required}
                  onChange={e => handleCheckChanged(e)}
                  className='require-check'
                />
                <label htmlFor={`required_${input.id}`}>{t('Required')}</label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default Section;
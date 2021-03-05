import React, {
  useState, useEffect, useLayoutEffect, useRef 
} from "react";
import { ConfirmModal } from "react-bootstrap4-modal";
import { default as ReactSelect } from "react-select";

export const option = ({ value, t, label: l, faClass }) => {
  const label = faClass ? <div>
    <div className='dropdown-text'>
      <i className={faClass}></i>
    </div>
    {t(l)}
  </div>
  : t(l);
  return {
    label,
    value
  }
}

export const langObject = (langs, value) => langs
  && langs.reduce((obj, item) => Object.assign(obj,
  {
    [item.code]: value
  }
), {});

/**
 * Keeps an eye on React rerenders
 * similar to componentWillReceiveProps or componentDidUpdate
 * @param {HTMLElement} value - current child's vale
 */
const usePrevious = value => {
  const prevChildrenRef = useRef();
  useEffect(() => {
    prevChildrenRef.current = value;
  }, [value]);

  return prevChildrenRef.current;
}

/**
 * Calculates the position of each child in the DOM
 * whenever children props change
 * @param {array} children - Component's children
 * @returns {object} - stores measurements of each child
 */

export const calculateBoundingBoxes = children => {
  const boundingBoxes = {};
  React.Children.forEach(children, child => {
    const domNode = child.ref.current;
    const nodeBoundingBox = domNode.getBoundingClientRect();

    boundingBoxes[child.key] = nodeBoundingBox;
  });

  return boundingBoxes;
};

/**
 * Animates the form page upon sections re-ordering
 * @param {object} props - Components children, applyTransition and it's setter
 * @returns {array} - the list of component's children
 */
export const AnimateSections = ({
  children,
  applyTransition
}) => {
  const [boundingBox, setBoundingBox] = useState({});
  const [prevBoundingBox, setPrevBoundingBox] = useState({});
  const prevChildren = usePrevious(children);

  useLayoutEffect(() => {
    const newBoundingBox = calculateBoundingBoxes(children);
    setBoundingBox(newBoundingBox);
  }, [children]);

  useLayoutEffect(() => {
    const prevBoundingBox = calculateBoundingBoxes(prevChildren);
    setPrevBoundingBox(prevBoundingBox);
  }, [prevChildren]);

  useEffect(() => {
    const hasPrevBoundingBox = Object.keys(prevBoundingBox).length;

    if (applyTransition && hasPrevBoundingBox) {
      React.Children.forEach(children, (child) => {
        const domNode = child.ref.current;
        const firstBox = prevBoundingBox[child.key]; //previous position
        const lastBox = boundingBox[child.key]; //current position
        const f = firstBox && firstBox.y;
        const l = lastBox && lastBox.y;
        let changeInY = f - l;
        // if (Math.abs(changeInY) > 700) {
        //   changeInY = changeInY > 0 ? 487.421875 : -487.421875;
        // }

        if (changeInY) {
          requestAnimationFrame(() => {
            // Before the DOM paints, invert child to old position
            domNode.style.transform = `translateY(${changeInY}px)`;
            domNode.style.transition = "transform 0s";

            requestAnimationFrame(() => {
              // After the previous frame, remove
              // the transistion to play the animation
              domNode.style.transform = "";
              domNode.style.transition = "transform 500ms";
            });
          });
        }
      });
    }
  }, [boundingBox, prevBoundingBox, children]);

  return children;
};


export const drag = (event, setDragId) => {
  setDragId(event.currentTarget.id);
}

export const drop = ({
  event,
  elements,
  dragId,
  setState,
  section,
  setAnimation,
  setSection,
  sections
}) => {
  const dragSection = elements.find( s => {
    return s.id === dragId
  });

  const dropSection = elements
    .find(e => e.id === event.currentTarget.id);

  if (!dragSection) return;

  const dragSectionOrder = dragSection.order;
  const dropSectionOrder = dropSection.order;

  const newEl = elements.map(s => {
    if (s.id === dragId) {
      s.order = dropSectionOrder;
    }
    if(s.id === event.currentTarget.id) {
      s.order = dragSectionOrder;
    }
    return s;
  }).sort((a,b) => a.order - b.order);
  
  if (section) {
    const newSections = sections.map(s => {
      if (s.id === section.id) {
        s.questions = newEl;
      }
      return s;
    })
    setSection(newSections);
  } else {
    setState(newEl);
  }
  setAnimation && setAnimation(true);
}

export const Modal = ({
  element, t, handleOkDelete, inputs,
  handleConfirm, sections, questions
}) => {
  const dependentSections = sections
    && sections.filter(s => s.depends_on_question_id === inputs.id);
  const dependentQestions = questions
    && questions.filter(q => q.depends_on_question_id === inputs.id);
  const questionsInSection = inputs.questions;
  const sectionDependency = questionsInSection && sections.find(s => {
    let isDependent = false;
    questionsInSection.forEach(q => {
      if (s.depends_on_question_id === q.id) {
        isDependent = true;
      }
    })
    return isDependent;
  })
  let message = `Are you sure you want to delete this ${element}?`;
  if (questionsInSection && sectionDependency) {
    message = 'One or more questions in this section is a dependency of other sections. Are you sure you still want to delete it?'
  } else if (dependentSections.length || dependentQestions.length) {
    message = 'This Question is a dependency of other sections/questions. Are you sure you still want to delete it?'
  }

  return(
    <ConfirmModal
      className='confirm-modal'
      visible={true}
      centered
      onOK={handleOkDelete}
      onCancel={() => handleConfirm()}
      okText={t("Yes - Delete")}
      cancelText={t("No - Don't delete")}>
      <p>
        {t(message)}
      </p>
    </ConfirmModal>
  )
}

/**
 * Handles move up or down of an element
 * @param {Object} - elements, index,setState, ... 
 */
export const handleMove = ({
  elements,
  index,
  setState,
  section,
  sections,
  setSection,
  isUp,
  setAnimation
}) => {
  const nEl = elements;

  if ((isUp && index !== 0) || (!isUp && index !== elements.length - 1)) {
  
    [nEl[isUp ? index - 1 : index + 1], nEl[index]] = [nEl[index], nEl[isUp ? index - 1 : index + 1]];
    const newEl = nEl.map((e, i) => {
      return {...e, order: i + 1}
    });
    
    if (section) {
      const newSections = sections.map(s => {
        if (s.id === section.id) {
          s = {...section, questions: newEl};
        }
        return s;
      })
      setSection(newSections);
    } else {
      setState(newEl);
    }
    setAnimation && setAnimation(true);
  }
}

export const Dependency = ({
  options, handlequestionDependency, inputs, lang,
  dependentQuestion, handleDependencyChange, t
}) => {
  const dependency = options.find(o => o.value === inputs.depends_on_question_id);
  
  return (
    <div className='dependency-wrapper'>
      <ReactSelect
        options={options}
        placeholder={t('Depends on question')}
        onChange={e => handlequestionDependency(e)}
        value={dependency ? dependency : null}
        className='select-dependency'
        styles={{
          control: (base, state) => ({
            ...base,
            boxShadow: "none",
            border: "none",
            transition: state.isFocused 
              && 'color,background-color 1.5s ease-out',
            background: state.isFocused
              && 'lightgray',
            color: '#fff'
          }),
          option: (base, state) => ({
            ...base,
            backgroundColor: state.isFocused
              && "lightgray",
            color: state.isFocused && "#fff"
          })
        }}
        menuPlacement="auto"
      />
      {dependentQuestion && dependentQuestion.type
        && dependentQuestion.type.value === 'single-choice'
        && (
        <div className='dependency-radio-wrapper'>
          <div className="min-wrapper">
            <input
              id='true-radio'
              type='radio'
              className='single-choice-check'
              checked={inputs.show_for_values}
              onChange={handleDependencyChange('single')}
              />
            <label htmlFor='true-radio'>
              {'True'}
            </label>
          </div>
          <div className="min-wrapper false-radio">
            <input
              id="false-radio"
              type='radio'
              className='single-choice-check'
              checked={!inputs.show_for_values}
              onChange={handleDependencyChange('single')}
              />
            <label htmlFor='false-radio'>
              {'False'}
            </label>
          </div>
        </div>
      )}
      {dependentQuestion && dependentQuestion.type
        && dependentQuestion.type.value === 'multi-choice'
        && dependentQuestion.options[lang].map((option, i) => (
        <div className='dependency-options-wrapper'>
          <input
            id={option.id}
            key={option.id}
            type='checkbox'
            className='single-choice-check'
            checked={inputs.show_for_values
              && inputs.show_for_values.length
              && inputs.show_for_values.includes(option.label)}
            onChange={handleDependencyChange(option.label)}
          />
          <label htmlFor={option.id}>{option.label}</label>
        </div>
      ))}
    </div>
  )
}

export const validationText = (min, max) => {
  if (max && !min) {
    return `You may enter no more that ${max} words`
  } else if (!max && min){
    return `You must enter at least ${min} words`
  } else if (max && min) {
    return `You must enter ${min} to ${max} words`
  } else {
    return '';
  }
}

export const Validation = ({
  t, options, inputs, lang, handleChange, sections, setSection
}) => {
  const [isFriendlyMode, setIsFriendlyMode] = useState(true);
  const maxMin = isFriendlyMode
    && inputs.validation_regex[lang]
    && inputs.validation_regex[lang].split('{')[1]
    && inputs.validation_regex[lang].split('{')[1].split(',');
  const max = maxMin && parseInt(maxMin[1].split('}')[0]);
  const min = maxMin && parseInt(maxMin[0]);

  const handleChangeMode = () => {
    setIsFriendlyMode(!isFriendlyMode);
  }

  return (
    <div className='validation-wrapper'>
      <span
        className='regex-label'
        >
          {t('Regular Expressions')}
        </span>
      <ReactSelect
        options={options}
        placeholder={t('Enter Mode')}
        onChange={handleChangeMode}
        defaultValue={options[0]}
        className='select-dependency select-validation'
        styles={{
          control: (base, state) => ({
            ...base,
            boxShadow: "none",
            border: "none",
            transition: state.isFocused 
              && 'color,background-color 1.5s ease-out',
            background: state.isFocused
              && 'lightgray',
            color: '#fff',
          }),
          option: (base, state) => ({
            ...base,
            backgroundColor: state.isFocused
              && "lightgray",
            color: state.isFocused && "#fff"
          })
        }}
        menuPlacement="auto"
      />
      {isFriendlyMode
        ? (
          <>
            <div className="min-wrapper">
              <label
                htmlFor="minimum"
                className="validation-label">
                {t('Min')}
              </label>
              <input
                id="minimum"
                name="minimum"
                type="number"
                className='validaion-input'
                placeholder={t('MIN')}
                onChange={handleChange('min')}
                min={0}
                />
            </div>
            <div className="min-wrapper">
              <label
                htmlFor="maximum"
                className="validation-label">
                {t('Max')}
              </label>
              <input
                id="maximum"
                name="maximum"
                type="number"
                onChange={handleChange('max')}
                className='validaion-input'
                placeholder={t('MAX')}
                min={min && min + 1}
                />
            </div>
          </>
        ) : (
          <div className="min-wrapper">
            <label
              htmlFor="regex"
              className="validation-label"
              >
              {t('Enter Your Regex')}
            </label>
            <input
              name="regex"
              id="regex"
              type="text"
              className='validaion-input advanced-regex'
              placeholder={t('Enter Your Regex')}
              onChange={handleChange('validation_regex')}
              value={t(inputs.validation_regex[lang])}
              />
          </div>
        )
      }
      <div className="min-wrapper">
        <label
          htmlFor="validation"
          className="validation-label"
          >
          {t('Validation Text')}
          </label>
        <input
          id="validation"
          name="validation"
          disabled={isFriendlyMode}
          type="text"
          className='validaion-text'
          placeholder={t('Validation Text')}
          value={t(inputs.validation_text[lang])}
          onChange={handleChange('validation_text')}
        />
      </div>
    </div>
  );
}

export const dependencyChange = ({
  prop, e, sections, inputs, setSection,
  sectionId, question
}) => {
  let updatedSections;
  if (prop === 'single') {
    if (question) {
      updatedSections = sections.map(s => {
        if (s.id === sectionId) {
          s = {...s, questions: s.questions.map(q => {
            if (q.id === inputs.id) {
              q = {...q, show_for_values: !q.show_for_values}
            }
            return q
          })}
        }
        return s
      });
    } else {
      updatedSections = sections.map(s => {
        if (s.id === inputs.id) {
          s = {...s, show_for_values: !s.show_for_values}
        }
        return s
      });
    }
  } else {
    if (question) {
      updatedSections = sections.map(s => {
        if (s.id === sectionId) {
          s = {...s, questions: s.questions.map(q => {
            if (q.id === inputs.id) {
              const showForValue  = q.show_for_values;
              if(e.target.checked) {
                q = {...q, show_for_values: showForValue && showForValue.length
                  ? !showForValue.includes(prop) && [...showForValue, prop]
                  : [prop] }
              }else {
                q = {...q, show_for_values: showForValue.filter(o => o !== prop)}
              }
            }
            return q
          })}
        }
        return s
      });
    } else {
      updatedSections = sections.map(s => {
        if (s.id === inputs.id) {
          const showForValue  = s.show_for_values;
          if(e.target.checked) {
            s = {...s, show_for_values: showForValue && showForValue.length
              ? !showForValue.includes(prop) && [...showForValue, prop]
              : [prop] }
          } else {
            s = {...s, show_for_values: showForValue.filter(o => o !== prop)}
          }
        }
        return s
      });
    }
  }
  setSection(updatedSections);
}

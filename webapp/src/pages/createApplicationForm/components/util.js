import React, {
  useState, useEffect, useLayoutEffect, useRef 
} from "react";
import { ConfirmModal } from "react-bootstrap4-modal";

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
  applyTransition,
  setApplytransition
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
        const f = firstBox && firstBox.top;
        const l = lastBox && lastBox.top;
        let changeInY = f - l;
        if (Math.abs(changeInY) > 700) {
          changeInY = changeInY > 0 ? 487.421875 : -487.421875;
        }

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
    setState({...section, questions: newEl});
    setSection(newSections);
  } else {
    setState(newEl);
  }
  setAnimation && setAnimation(true);
}

export const Modal = ({
  element, t, handleOkDelete,
  handleConfirm
}) => (
  <ConfirmModal
    className='confirm-modal'
    visible={true}
    centered
    onOK={handleOkDelete}
    onCancel={() => handleConfirm()}
    okText={t("Yes - Delete")}
    cancelText={t("No - Don't delete")}>
    <p>
      {t(`Are you sure you want to delete this ${element}?`)}
    </p>
  </ConfirmModal>
)

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
  u,
  setAnimation
}) => {
  const nEl = elements;
  if ((u && index !== 0) || (!u && index !== elements.length - 1)) {
    [nEl[u ? index - 1 : index + 1], nEl[index]] = [nEl[index], nEl[u ? index - 1 : index + 1]];
    const newEl = nEl.map((e, i) => {
      return {...e, order: i + 1}
    });
    if (section) {
      const newSections = sections.map(s => {
        if (s.id === section.id) {
          s.questions = newEl;
        }
        return s;
      })
      setState({...section, questions: newEl})
      setSection(newSections);
    } else {
      setState(newEl);
    }
    setAnimation && setAnimation(true);
  } 
}

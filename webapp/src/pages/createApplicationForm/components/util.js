import React, { useState, useEffect, useLayoutEffect, useRef, forwardRef } from "react";

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

const usePrevious = value => {
  const prevChildrenRef = useRef();
  useEffect(() => {
    prevChildrenRef.current = value;
  }, [value]);

  return prevChildrenRef.current;
}

// const calculateBoundingBox = children => {
//   const boundingBoxes = {};

//   React.Children.forEach(children, child => {
//     const domNode = child.ref.current;
//     const nodeBoundingBox = domNode.getBoundingClientRect();

//     boundingBoxes[child.key] = nodeBoundingBox;
//   });

//   return boundingBoxes;
// }


export const calculateBoundingBoxes = children => {
  const boundingBoxes = {};

  React.Children.forEach(children, child => {
    const domNode = child.ref.current;
    const nodeBoundingBox = domNode.getBoundingClientRect();

    boundingBoxes[child.key] = nodeBoundingBox;
  });

  return boundingBoxes;
};

// export const AnimationReorder = ({ children }) => {
//   // console.log('*)*)*)*)*)* children ', children);
//   const [boundingBox, setBoundingBox] = useState({});
//   const [prevBoundingBox, setPrevBoundingBox] = useState({});
//   const prevChildren = usePrevious(children);

//   useLayoutEffect(() => {
//     const newBoundingBox = calculateBoundingBoxes(children);
//     setBoundingBox(newBoundingBox);
//   }, [children]);

//   useLayoutEffect(() => {
//     const prevBoundingBox = calculateBoundingBoxes(prevChildren);
//     setPrevBoundingBox(prevBoundingBox);
//   }, [prevChildren]);

//   useEffect(() => {
//     const hasPrevBoundingBox = Object.keys(prevBoundingBox).length;
//     // console.log('------- prev bounfding box', prevBoundingBox);
//     if(hasPrevBoundingBox) {
//       React.Children.forEach(children, child => {
//         const domNode = child.ref.current;
//         const firstBox = prevBoundingBox[child.key];
//         const lastBox = boundingBox[child.key];
//         const changeInX = firstBox.y - lastBox.y;
//         // console.log('------- first box', firstBox, lastBox);

//         if (!changeInX) {
//           // console.log('------- change In X', domNode);
//           requestAnimationFrame(() => {
//             // Before the DOM paints, invert child to old position
//             domNode.style.transform = `translateY(${changeInX}px)`;
//             domNode.style.transition = "transform 0s";

//             requestAnimationFrame(() => {
//               // After the previous frame, remove
//               // the transistion to play the animation
//               domNode.style.transform = "";
//               domNode.style.transition = "transform 500ms";
//             });
//           });
//         }
//       });
//     }
//   }, [boundingBox, prevBoundingBox, children]);

//   return children;
// }

export const AnimateBubbles = ({ children, applyTransition, setApplytransition }) => {
  console.log('________anime ', applyTransition);
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
        const firstBox = prevBoundingBox[child.key];
        const lastBox = boundingBox[child.key];
        const f = firstBox && firstBox.top;
        const l = lastBox && lastBox.top;
        const changeInX = f - l;

        if (changeInX) {
          requestAnimationFrame(() => {
            // Before the DOM paints, invert child to old position
            domNode.style.transform = `translateY(${changeInX}px)`;
            domNode.style.transition = "transform 0s";

            requestAnimationFrame(() => {
              // After the previous frame, remove
              // the transistion to play the animation
              domNode.style.transform = "";
              domNode.style.transition = "transform 500ms";
            });
            setApplytransition(false);
          });
        }
      });
    }
  }, [boundingBox, prevBoundingBox, children]);

  return children;
};

export function shuffleArray(array) {
  return array
    .map(a => ({ sort: Math.random(), value: a }))
    .sort((a, b) => a.sort - b.sort)
    .map(a => a.value);
}

const IMAGE_URL = "https://loremflickr.com/120/120/sun";

export const Bubble = forwardRef(({ text, id }, ref) => (
  <div ref={ref}>
    <div className="circle">
      <span
        className="image"
        style={{
          backgroundImage: `url('${IMAGE_URL}?random=${id}')`
        }}
      />
    </div>
    <p className="text">{text}</p>
  </div>
));

export const initialImages =  [
  { id: "1", text: "Image 1" },
  { id: "2", text: "Image 2" },
  { id: "3", text: "Image 3" },
  { id: "4", text: "Image 4" },
  { id: "5", text: "Image 5" }
];

import React from "react";
import ReactMarkdown from 'react-markdown';

import remarkMath from "remark-math";
import MathJax from "react-mathjax";

import gfm from "remark-gfm";

function MarkdownRenderer(props) {
    const newProps = {
        ...props,
        plugins: [remarkMath],
        remarkPlugins: [gfm],
        renderers: {
            ...props.renderers,
            math: (props) => <MathJax.Node formula={props.value} />,
            inlineMath: (props) => <MathJax.Node inline formula={props.value} />,
            link: (props) => <a href={props.href} target="_blank" rel="noopener noreferrer">{props.children}</a>
        }
      };

      return (
        <MathJax.Provider input="tex">
            <ReactMarkdown {...newProps} />
        </MathJax.Provider>
      );

}

export default MarkdownRenderer
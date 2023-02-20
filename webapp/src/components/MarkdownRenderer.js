import React from "react";
import ReactMarkdown from 'react-markdown';

import remarkMath from "remark-math";
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

import gfm from "remark-gfm";

function MarkdownRenderer(props) {
    const newProps = {
        ...props,
        plugins: [remarkMath],
        remarkPlugins: [gfm],
        renderers: {
            ...props.renderers,
            math: (props) => <BlockMath math={props.value}/>,
            inlineMath: (props) => <InlineMath math={props.value}/>,
            link: (props) => <a href={props.href} target="_blank" rel="noopener noreferrer">{props.children}</a>
        }
      };

      return (
        <div className="markdown-container"><ReactMarkdown {...newProps} /></div>
      );

}

export default MarkdownRenderer
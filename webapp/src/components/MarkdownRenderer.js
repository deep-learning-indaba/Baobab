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
            math: (props) => <span><BlockMath math={props.value}/></span>,
            inlineMath: (props) => <span><InlineMath math={props.value}/></span>,
            link: (props) => <a href={props.href} target="_blank" rel="noopener noreferrer">{props.children}</a>
        }
      };

      return (
        <div class="markdown-container"><ReactMarkdown {...newProps} /></div>
      );

}

export default MarkdownRenderer
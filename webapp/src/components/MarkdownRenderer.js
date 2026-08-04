import React from "react";
import ReactMarkdown from 'react-markdown';
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import 'katex/dist/katex.min.css';
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";

var AS_FRAGMENT = ({ children: c }) => <React.Fragment>{c}</React.Fragment>;
// Block-level tags collapsed to inline when a single-line context (e.g. a
// heading) can't legally contain a <div>/<p>/<h1> without breaking the DOM.
var INLINE_TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'];

function MarkdownRenderer({ source, children, components, inline, ...props }) {
    var Wrapper = inline ? 'span' : 'div';
    var defaultComponents = {
        a: ({ href, children: linkChildren }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">{linkChildren}</a>
        ),
    };
    if (inline) {
        INLINE_TAGS.forEach(function (tag) { defaultComponents[tag] = AS_FRAGMENT; });
    }
    return (
        <Wrapper className="markdown-container">
            <ReactMarkdown
                {...props}
                remarkPlugins={[remarkMath, remarkGfm, remarkBreaks]}
                rehypePlugins={[rehypeKatex]}
                components={{ ...defaultComponents, ...components }}
            >
                {source || children}
            </ReactMarkdown>
        </Wrapper>
    );
}

export default MarkdownRenderer;

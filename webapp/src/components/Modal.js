import React from 'react';

export class ConfirmModal extends React.Component {
    render() {
        const { visible, onOK, onCancel, okText, cancelText, children } = this.props;
        if (!visible) return null;

        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
                <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-border space-y-6 animate-in fade-in zoom-in-95 duration-150 text-left">
                    <div className="text-foreground text-sm leading-relaxed">
                        {children}
                    </div>
                    <div className="flex justify-end gap-3">
                        <button
                            type="button"
                            className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold transition-colors bg-secondary text-secondary-foreground hover:bg-secondary/80 cursor-pointer"
                            onClick={onCancel}
                        >
                            {cancelText || "Cancel"}
                        </button>
                        <button
                            type="button"
                            className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 cursor-pointer"
                            onClick={onOK}
                        >
                            {okText || "OK"}
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}

export default class Modal extends React.Component {
    render() {
        const { visible, onClickBackdrop, children } = this.props;
        if (!visible) return null;

        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
                <div className="absolute inset-0" onClick={onClickBackdrop}></div>
                
                <div className="relative bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-border space-y-4 animate-in fade-in zoom-in-95 duration-150 text-left">
                    {children}
                </div>
            </div>
        );
    }
}

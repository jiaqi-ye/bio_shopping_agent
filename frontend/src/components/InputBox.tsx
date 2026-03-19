import { useEffect, useRef, useState } from "react";

type InputBoxProps = {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
};

export default function InputBox({ value, onChange, onSend, disabled }: InputBoxProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const valueRef = useRef<string>(value);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = "0px";
    const nextHeight = Math.min(textareaRef.current.scrollHeight, 200);
    textareaRef.current.style.height = `${nextHeight}px`;
  }, [value]);

  useEffect(() => {
    const SpeechRecognitionImpl =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionImpl) {
      setSpeechSupported(false);
      return;
    }
    setSpeechSupported(true);
    const recognition: SpeechRecognition = new SpeechRecognitionImpl();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      const nextValue = valueRef.current
        ? `${valueRef.current} ${transcript}`
        : transcript;
      onChange(nextValue.trim());
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognitionRef.current = recognition;
    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, [onChange]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-3xl px-6 py-4">
        <div className="flex items-end gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask for vendors, lead times, or a new RFQ..."
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => {
              if (!speechSupported || disabled) return;
              if (isListening) {
                recognitionRef.current?.stop();
                setIsListening(false);
                return;
              }
              recognitionRef.current?.start();
              setIsListening(true);
            }}
            disabled={disabled || !speechSupported}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-300"
          >
            {isListening ? "Listening..." : "Speak"}
          </button>
          <button
            type="button"
            onClick={onSend}
            disabled={disabled || !value.trim()}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            Send
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-400">
          Press Enter to send, Shift + Enter for a new line.
        </p>
      </div>
    </div>
  );
}

/// <reference types="vite/client" />


type SpeechRecognition = any;
type SpeechRecognitionEvent = any;

declare interface Window {
  SpeechRecognition?: new () => SpeechRecognition;
  webkitSpeechRecognition?: new () => SpeechRecognition;
}

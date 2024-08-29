import { Example } from "./Example";

import styles from "./Example.module.css";

const DEFAULT_EXAMPLES: string[] = [
  "How to get better sleep?",
  "What are some things I should take note of when I am pregnant?",
  "How do I lower my chances of getting diabetes?"
];

const GPT4V_EXAMPLES: string[] = ["Lorem Ipsum", "Lorem Ipsum", "Lorem Ipsum"];

interface Props {
  onExampleClicked: (value: string) => void;
  useGPT4V?: boolean;
}

export const ExampleList = ({ onExampleClicked, useGPT4V }: Props) => {
  return (
    <ul className={styles.examplesNavList}>
      {(useGPT4V ? GPT4V_EXAMPLES : DEFAULT_EXAMPLES).map((question, i) => (
        <li key={i}>
          <Example text={question} value={question} onClick={onExampleClicked} />
        </li>
      ))}
    </ul>
  );
};

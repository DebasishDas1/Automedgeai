import { useEffect, useState } from "react";

export default function useTypewriter(words: string[], speed = 90, pause = 1500) {
  const [index, setIndex] = useState(0);
  const [sub, setSub] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const word = words[index];

    const timeout = setTimeout(() => {
      if (!deleting) {
        setSub(word.substring(0, sub.length + 1));

        if (sub === word) {
          setTimeout(() => setDeleting(true), pause);
        }
      } else {
        setSub(word.substring(0, sub.length - 1));

        if (sub === "") {
          setDeleting(false);
          setIndex((i) => (i + 1) % words.length);
        }
      }
    }, deleting ? speed / 2 : speed);

    return () => clearTimeout(timeout);
  }, [sub, deleting, index]);

  return sub;
}
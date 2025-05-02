import React, { useState, useEffect } from "react";

interface TypeWriterProps extends React.HTMLAttributes<HTMLSpanElement> {
  text: string;
  speed?: number; // ms per character
  startDelay?: number; // ms before typing starts
  startOnView?: boolean; // if true, only start when prop is true
  className?: string;
}

const TypeWriter: React.FC<TypeWriterProps> = ({
  text,
  speed = 30,
  startDelay = 0,
  startOnView = true,
  className,
  ...rest
}) => {
  const [displayed, setDisplayed] = useState("");
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (startOnView && !started) {
      setStarted(true);
    }
  }, [startOnView, started]);

  useEffect(() => {
    let timeout: NodeJS.Timeout;

    if (started && displayed.length < text.length) {
      timeout = setTimeout(() => {
        setDisplayed((prev) => prev + text[prev.length]);
      }, displayed.length === 0 ? startDelay : speed);
    }

    return () => clearTimeout(timeout);
  }, [started, displayed, text, speed, startDelay]);

  return (
    <span className={className} {...rest}>
      {displayed}
      <span className="typewriter-cursor" style={{ opacity: 0.7 }}>|</span>
    </span>
  );
};

export default TypeWriter;


import React, { useEffect, useState } from 'react';

interface StreamingTextProps {
  text: string;
  className?: string;
  speed?: number; // Characters per second
  onComplete?: () => void;
}

const StreamingText: React.FC<StreamingTextProps> = ({
  text,
  className = '',
  speed = 30,
  onComplete,
}) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    setDisplayedText('');
    setIsComplete(false);
    
    if (!text) {
      setIsComplete(true);
      onComplete?.();
      return;
    }

    let currentIndex = 0;
    const interval = 1000 / speed; // Time per character in milliseconds

    const timer = setInterval(() => {
      if (currentIndex < text.length) {
        setDisplayedText(prev => prev + text[currentIndex]);
        currentIndex++;
      } else {
        clearInterval(timer);
        setIsComplete(true);
        onComplete?.();
      }
    }, interval);

    return () => clearInterval(timer);
  }, [text, speed, onComplete]);

  return (
    <div className={className}>
      {displayedText}
      {!isComplete && (
        <span className="inline-block w-1 h-4 ml-1 bg-twisty-primary animate-pulse" />
      )}
    </div>
  );
};

export default StreamingText;

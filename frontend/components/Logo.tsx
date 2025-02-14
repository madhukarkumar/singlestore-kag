import React from 'react';

const Logo = ({ className = '', size = 32 }: { className?: string; size?: number }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Outer cube */}
      <g fill="none" stroke="currentColor" strokeWidth="1">
        {/* Front face */}
        <path d="M20,20 L80,20 L80,80 L20,80 Z" />
        {/* Top face */}
        <path d="M20,20 L35,5 L95,5 L80,20" />
        {/* Right face */}
        <path d="M80,20 L95,5 L95,65 L80,80" />
        
        {/* Inner cube structure */}
        <path d="M35,35 L65,35 L65,65 L35,65 Z" />
        <path d="M35,35 L42.5,27.5 L72.5,27.5 L65,35" />
        <path d="M65,35 L72.5,27.5 L72.5,57.5 L65,65" />
        
        {/* Connecting lines */}
        <path d="M20,50 L35,50" />
        <path d="M65,50 L80,50" />
        <path d="M50,20 L50,35" />
        <path d="M50,65 L50,80" />
        
        {/* Additional grid lines */}
        <path d="M35,20 L42.5,5" />
        <path d="M50,20 L57.5,5" />
        <path d="M65,20 L72.5,5" />
        <path d="M35,80 L42.5,65" />
        <path d="M50,80 L57.5,65" />
        <path d="M65,80 L72.5,65" />
        
        {/* Dots at intersections */}
        <g fill="currentColor">
          <circle cx="20" cy="20" r="1" />
          <circle cx="35" cy="5" r="1" />
          <circle cx="80" cy="20" r="1" />
          <circle cx="95" cy="5" r="1" />
          <circle cx="20" cy="80" r="1" />
          <circle cx="80" cy="80" r="1" />
          <circle cx="95" cy="65" r="1" />
          
          {/* Inner cube dots */}
          <circle cx="35" cy="35" r="1" />
          <circle cx="65" cy="35" r="1" />
          <circle cx="35" cy="65" r="1" />
          <circle cx="65" cy="65" r="1" />
          <circle cx="42.5" cy="27.5" r="1" />
          <circle cx="72.5" cy="27.5" r="1" />
          <circle cx="72.5" cy="57.5" r="1" />
        </g>
      </g>
    </svg>
  );
};

export default Logo;

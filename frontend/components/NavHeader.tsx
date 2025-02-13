"use client"; 

import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";

function NavHeader() {
  const [position, setPosition] = useState({
    left: 0,
    width: 0,
    opacity: 0,
  });

  return (
    <ul
      className="relative mx-auto flex w-fit rounded-full border-2 border-black bg-white p-1"
      onMouseLeave={() => setPosition((pv) => ({ ...pv, opacity: 0 }))}
    >
      <Tab href="/" setPosition={setPosition}>Home</Tab>
      <Tab href="/new-home" setPosition={setPosition}>Knowledge Base</Tab>
      <Tab href="/search" setPosition={setPosition}>Search</Tab>
      <Tab href="/graph" setPosition={setPosition}>Graph</Tab>
      <Tab href="/upload" setPosition={setPosition}>Upload</Tab>

      <Cursor position={position} />
    </ul>
  );
}

const Tab = ({
  children,
  setPosition,
  href,
}: {
  children: React.ReactNode;
  setPosition: any;
  href: string;
}) => {
  const ref = useRef<HTMLLIElement>(null);
  return (
    <li
      ref={ref}
      onMouseEnter={() => {
        if (!ref.current) return;

        const { width } = ref.current.getBoundingClientRect();
        setPosition({
          width,
          opacity: 1,
          left: ref.current.offsetLeft,
        });
      }}
      className="relative z-10 block cursor-pointer px-3 py-1.5 text-xs uppercase text-white mix-blend-difference md:px-5 md:py-3 md:text-base"
    >
      <Link href={href}>{children}</Link>
    </li>
  );
};

function Cursor({ position }: { position: any }) {
  return (
    <motion.div
      className="absolute inset-0 z-0 rounded-full bg-black"
      animate={position}
      transition={{
        type: "spring",
        stiffness: 350,
        damping: 25,
      }}
    />
  );
}

export default NavHeader;

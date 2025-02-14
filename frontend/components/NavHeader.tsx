"use client"; 

import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Logo from "./Logo";

function NavHeader() {
  const [position, setPosition] = useState({
    left: 0,
    width: 0,
    opacity: 0,
  });

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Logo className="text-gray-800" size={32} />
          <h1 className="text-2xl font-semibold text-gray-800">
            SingleStore Prime Radian
          </h1>
        </div>
        <ul
          className="relative flex w-fit rounded-full border-2 border-black bg-white p-1"
          onMouseLeave={() => setPosition((pv) => ({ ...pv, opacity: 0 }))}
        >
          <Tab href="/" setPosition={setPosition}>Home</Tab>
          <Tab href="/kb" setPosition={setPosition}>Knowledge Base</Tab>
          <Tab href="/kb/upload" setPosition={setPosition}>Upload</Tab>
          <Tab href="/config" setPosition={setPosition}>Search Settings</Tab>

          <Cursor position={position} />
        </ul>
      </div>
    </header>
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

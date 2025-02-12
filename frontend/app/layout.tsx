import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SingleStore Knowledge Graph Search",
  description: "Search through documents using SingleStore's vector and text search capabilities",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="bg-gray-800">
          <nav className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <Link href="/" className="text-white font-bold text-xl">
                  SingleStore KAG
                </Link>
                <div className="ml-10 flex items-baseline space-x-4">
                  <Link
                    href="/"
                    className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Search
                  </Link>
                  <Link
                    href="/kb"
                    className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    KB Stats
                  </Link>
                  <Link
                    href="/kb/upload"
                    className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Upload
                  </Link>
                  <Link
                    href="/config"
                    className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Settings
                  </Link>
                </div>
              </div>
            </div>
          </nav>
        </div>
        {children}
      </body>
    </html>
  );
}

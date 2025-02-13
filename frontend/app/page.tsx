'use client';

import SearchForm from '../components/SearchForm';
import NavHeader from '@/components/NavHeader';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <NavHeader />
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Welcome to SingleStore Prime Radian
          </h2>
          <p className="mt-4 text-lg leading-8 text-gray-600">
            Powered by vector search and AI
          </p>
        </div>
      </div>
    </main>
  );
}

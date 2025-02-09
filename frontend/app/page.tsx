'use client';

import SearchForm from '../components/SearchForm';

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <main className="max-w-4xl mx-auto p-8">
        <h1 className="text-3xl font-bold mb-8 text-center">
          SingleStore Knowledge Graph Search
        </h1>
        <SearchForm />
      </main>
    </div>
  );
}

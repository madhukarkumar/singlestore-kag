'use client';

import NavHeader from '@/components/NavHeader';
import UploadForm from '@/components/UploadForm';

export default function Upload() {
  return (
    <main className="min-h-screen bg-gray-50">
      <NavHeader />
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <UploadForm />
        </div>
      </div>
    </main>
  );
}

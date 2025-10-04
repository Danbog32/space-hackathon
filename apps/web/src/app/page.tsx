import Link from "next/link";
import { DatasetList } from "@/components/DatasetList";

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 text-center">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Astro-Zoom
          </h1>
          <p className="text-xl text-gray-400">
            Explore gigantic NASA images with deep zoom, annotations, and AI search
          </p>
        </header>

        <section className="mb-12">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Available Datasets</h2>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Upload Image
            </Link>
          </div>
          <DatasetList />
        </section>

        <footer className="mt-16 text-center text-sm text-gray-500">
          <p>Built for 36-hour hackathon • OpenSeadragon • CLIP • FAISS</p>
        </footer>
      </div>
    </main>
  );
}

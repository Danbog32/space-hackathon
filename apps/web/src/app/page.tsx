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
          <h2 className="text-2xl font-semibold mb-6">Available Datasets</h2>
          <DatasetList />
        </section>

        <footer className="mt-16 text-center text-sm text-gray-500">
          <p>Built for 36-hour hackathon • OpenSeadragon • CLIP • FAISS</p>
        </footer>
      </div>
    </main>
  );
}

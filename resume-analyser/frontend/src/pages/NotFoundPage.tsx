import { Link } from 'react-router-dom'
import { Home, Search } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center text-center px-4">
      <div>
        <p className="text-8xl font-black text-gray-100">404</p>
        <h1 className="text-2xl font-bold text-gray-800 mt-4">Page not found</h1>
        <p className="text-gray-500 mt-2 text-sm">The page you're looking for doesn't exist.</p>
        <div className="flex gap-3 justify-center mt-8">
          <Link to="/" className="btn-primary flex items-center gap-2">
            <Home className="w-4 h-4" /> Go Home
          </Link>
          <Link to="/analyse" className="btn-secondary flex items-center gap-2">
            <Search className="w-4 h-4" /> Analyse Resume
          </Link>
        </div>
      </div>
    </div>
  )
}

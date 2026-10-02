import { Loader2 } from 'lucide-react'

/** Full-height spinner shown while a lazy route chunk is loading. */
export default function RouteFallback() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center text-gray-400">
      <Loader2 className="w-8 h-8 animate-spin" />
    </div>
  )
}

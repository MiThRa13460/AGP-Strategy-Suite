import { useRef, useEffect } from 'react'

interface GForceTraceProps {
  gLat: number
  gLong: number
  maxG?: number
}

export function GForceTrace({ gLat, gLong, maxG = 3 }: GForceTraceProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const trailRef = useRef<Array<{ x: number; y: number; age: number }>>([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const size = canvas.width
    const center = size / 2
    const scale = (size / 2 - 20) / maxG

    // Add current point to trail
    trailRef.current.push({
      x: gLat,
      y: -gLong, // Invert so acceleration is up
      age: 0
    })

    // Keep only last 50 points
    if (trailRef.current.length > 50) {
      trailRef.current.shift()
    }

    // Age all points
    trailRef.current.forEach(p => p.age++)

    // Clear canvas
    ctx.clearRect(0, 0, size, size)

    // Draw grid circles
    ctx.strokeStyle = '#1a1a2e'
    ctx.lineWidth = 1

    for (let g = 1; g <= maxG; g++) {
      ctx.beginPath()
      ctx.arc(center, center, g * scale, 0, Math.PI * 2)
      ctx.stroke()
    }

    // Draw crosshairs
    ctx.beginPath()
    ctx.moveTo(10, center)
    ctx.lineTo(size - 10, center)
    ctx.moveTo(center, 10)
    ctx.lineTo(center, size - 10)
    ctx.stroke()

    // Draw G labels
    ctx.fillStyle = '#666'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    for (let g = 1; g <= maxG; g++) {
      ctx.fillText(`${g}g`, center + g * scale + 12, center + 4)
    }

    // Draw trail
    ctx.lineCap = 'round'
    for (let i = 1; i < trailRef.current.length; i++) {
      const p1 = trailRef.current[i - 1]
      const p2 = trailRef.current[i]
      const alpha = 1 - (p2.age / 50)

      ctx.strokeStyle = `rgba(0, 255, 136, ${alpha * 0.5})`
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(center + p1.x * scale, center + p1.y * scale)
      ctx.lineTo(center + p2.x * scale, center + p2.y * scale)
      ctx.stroke()
    }

    // Draw current position
    const x = center + gLat * scale
    const y = center - gLong * scale

    // Glow effect
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, 15)
    gradient.addColorStop(0, 'rgba(0, 255, 136, 0.8)')
    gradient.addColorStop(1, 'rgba(0, 255, 136, 0)')
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(x, y, 15, 0, Math.PI * 2)
    ctx.fill()

    // Main dot
    ctx.fillStyle = '#00ff88'
    ctx.beginPath()
    ctx.arc(x, y, 6, 0, Math.PI * 2)
    ctx.fill()

    // White center
    ctx.fillStyle = '#fff'
    ctx.beginPath()
    ctx.arc(x, y, 3, 0, Math.PI * 2)
    ctx.fill()

  }, [gLat, gLong, maxG])

  const totalG = Math.sqrt(gLat * gLat + gLong * gLong)

  return (
    <div className="bg-agp-card border border-agp-border rounded-lg p-6">
      <h3 className="text-sm text-gray-400 mb-4">G-Forces</h3>

      <div className="flex flex-col items-center">
        <canvas
          ref={canvasRef}
          width={200}
          height={200}
          className="mb-4"
        />

        <div className="grid grid-cols-3 gap-4 w-full text-center">
          <div>
            <div className="text-xs text-gray-500">Lateral</div>
            <div className={`text-lg font-bold ${
              Math.abs(gLat) > 2 ? 'text-agp-accent' : 'text-white'
            }`}>
              {gLat > 0 ? '+' : ''}{gLat.toFixed(2)}g
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Total</div>
            <div className={`text-lg font-bold ${
              totalG > 2.5 ? 'text-agp-accent' : 'text-white'
            }`}>
              {totalG.toFixed(2)}g
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Long.</div>
            <div className={`text-lg font-bold ${
              Math.abs(gLong) > 1.5 ? 'text-agp-accent' : 'text-white'
            }`}>
              {gLong > 0 ? '+' : ''}{gLong.toFixed(2)}g
            </div>
          </div>
        </div>

        <div className="mt-2 text-xs text-gray-500">
          {gLong > 0.5 ? '⬆️ Acceleration' : gLong < -0.5 ? '⬇️ Freinage' : ''}
          {gLat > 0.5 ? ' ➡️ Droite' : gLat < -0.5 ? ' ⬅️ Gauche' : ''}
        </div>
      </div>
    </div>
  )
}

export default GForceTrace

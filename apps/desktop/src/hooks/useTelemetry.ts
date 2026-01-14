import { useCallback, useRef, useEffect } from 'react'
import { useTelemetryStore } from '../stores/telemetryStore'

const WS_URL = 'ws://localhost:8765'

export function useTelemetry() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)

  const {
    setConnected,
    setRf2Connected,
    setTelemetry,
    setAnalysis,
    setRecommendations,
    reset,
  } = useTelemetryStore()

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'status':
          setConnected(true)
          if (data.connected !== undefined) {
            setRf2Connected(data.connected)
          }
          break

        case 'rf2_connected':
          setRf2Connected(data.connected)
          break

        case 'telemetry':
          setTelemetry(data)
          if (data.analysis) {
            setAnalysis(data.analysis)
          }
          break

        case 'recommendations':
          setRecommendations(data.data)
          break

        case 'summary':
          setAnalysis(data.data)
          break

        case 'error':
          console.error('[AGP] Server error:', data.message)
          break

        default:
          break
      }
    } catch (e) {
      console.error('[AGP] Failed to parse message:', e)
    }
  }, [setConnected, setRf2Connected, setTelemetry, setAnalysis, setRecommendations])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        console.log('[AGP] Connected to backend')
        setConnected(true)

        // Request initial status
        ws.send(JSON.stringify({ type: 'get_status' }))
      }

      ws.onmessage = handleMessage

      ws.onclose = () => {
        console.log('[AGP] Disconnected from backend')
        setConnected(false)
        setRf2Connected(false)

        // Reconnect after delay
        reconnectTimeoutRef.current = window.setTimeout(() => {
          console.log('[AGP] Attempting to reconnect...')
          connect()
        }, 2000)
      }

      ws.onerror = (error) => {
        console.error('[AGP] WebSocket error:', error)
      }

      wsRef.current = ws
    } catch (e) {
      console.error('[AGP] Failed to connect:', e)

      // Retry connection
      reconnectTimeoutRef.current = window.setTimeout(connect, 2000)
    }
  }, [handleMessage, setConnected, setRf2Connected])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    reset()
  }, [reset])

  const send = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const requestRecommendations = useCallback(() => {
    send({ type: 'get_recommendations' })
  }, [send])

  const requestSummary = useCallback(() => {
    send({ type: 'get_summary' })
  }, [send])

  const loadSetup = useCallback((path: string) => {
    send({ type: 'load_setup', path })
  }, [send])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    connect,
    disconnect,
    send,
    requestRecommendations,
    requestSummary,
    loadSetup,
  }
}

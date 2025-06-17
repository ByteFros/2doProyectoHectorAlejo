// hooks/useTripDays.ts
import { useState, useEffect } from 'react'
import useAuth from '~/components/hooks/use-auth'
import { apiFetch } from '~/utils/api'

export interface TripDay {
  id: number
  fecha: string      // "YYYY-MM-DD"
  exento: boolean
  revisado: boolean
}

export default function useTripDays(tripId?: number) {
  const { token } = useAuth()
  const [data, setData] = useState<TripDay[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token || !tripId) {
      setLoading(false)
      return
    }
    
    setLoading(true)

    const fetchTripDays = async () => {
      try {
        const response = await apiFetch(`/api/users/viajes/${tripId}/dias/`, {
          method: 'GET',
        }, true) // Pasamos true para indicar que requiere auth

        if (!response.ok) {
          throw new Error('No se pudieron cargar los días del viaje')
        }

        const days = await response.json()
        setData(days)
      } catch (error) {
        console.error('❌ Error al cargar días del viaje:', error)
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchTripDays()
  }, [token, tripId])

  return { data, loading }
}
// hooks/useTripDays.ts
import { useState, useEffect } from 'react'
import useAuth from '~/components/hooks/use-auth'

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
    if (!token || !tripId) return
    setLoading(true)

    fetch(`http://127.0.0.1:8000/api/users/viajes/${tripId}/dias/`, {
      headers: { Authorization: `Token ${token}`, 'Content-Type': 'application/json' },
    })
    .then(r => {
      if (!r.ok) throw new Error('No pude cargar los días')
      return r.json()
    })
    .then((days: TripDay[]) => setData(days))
    .catch(console.error)
    .finally(() => setLoading(false))
  }, [token, tripId])

  return { data, loading }
}

// hooks/useUpdateTripDay.ts
import { useState } from 'react'
import useAuth from '~/components/hooks/use-auth'
import { buildApiUrl } from '@config/api'

export default function useUpdateTripDay() {
  const { token } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  // hooks/useUpdateTripDay.ts
  function updateDay(tripId: number, dayId: number, exento: boolean) {
    setLoading(true)
    setError(null)

    return fetch(
      buildApiUrl(`/users/viajes/${tripId}/dias/${dayId}/`),
      {
        method: 'PUT',
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ exento, revisado: true })
      }
    )
      .then(r => {
        if (!r.ok) throw new Error('No pude actualizar el día')
        return r.json()
      })
      .finally(() => setLoading(false))
  }

  return { updateDay, loading, error }
}

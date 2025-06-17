// hooks/useTripNotes.ts
import { useState, useEffect } from "react";
import { apiFetch } from "~/utils/api"; // Ajusta el path si cambia
import useAuth from "./use-auth";

export interface Nota {
  id: number;
  contenido: string;
  fecha_creacion: string;
}

export function useTripNotes(tripId: number | null) {
  const { token } = useAuth();
  const [notes, setNotes] = useState<Nota[]>([]);

  useEffect(() => {
    if (!token || !tripId) {
      console.log("🚫 No se puede cargar notas. token o tripId faltante", { token, tripId });
      return;
    }

    console.log("📥 Cargando notas para el viaje:", tripId);

    const fetchNotes = async () => {
      try {
        const res = await apiFetch(`/api/users/notas/${tripId}/`, {}, true);
        if (!res.ok) throw new Error("Error al cargar notas");

        const data = await res.json();
        console.log("✅ Notas obtenidas:", data);
        setNotes(data);
      } catch (err) {
        console.error("❌ Error al obtener notas:", err);
      }
    };

    fetchNotes();
  }, [tripId, token]);

  const createNote = async (texto: string) => {
    if (!token || !tripId) {
      console.warn("⚠️ No se puede crear nota. Faltan datos:", { token, tripId });
      return;
    }

    try {
      const res = await apiFetch(
        `/api/users/notas/${tripId}/`,
        {
          method: "POST",
          body: JSON.stringify({ contenido: texto }),
        },
        true
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Error al guardar nota");
      }

      const nuevaNota = await res.json();
      console.log("📝 Nota creada:", nuevaNota);
      setNotes(prev => [nuevaNota, ...prev]);
    } catch (err) {
      console.error("❌ Error al crear nota:", err);
    }
  };

  const deleteNote = async (noteId: number) => {
    if (!token || !tripId) return;

    try {
      const res = await apiFetch(
        `/api/users/notas/${tripId}/${noteId}/`,
        { method: "DELETE" },
        true
      );

      if (!res.ok) throw new Error("Error al eliminar nota");

      setNotes((prev) => prev.filter((n) => n.id !== noteId));
    } catch (err) {
      console.error("❌ Error al eliminar nota:", err);
    }
  };

  return { notes, createNote, deleteNote };
}

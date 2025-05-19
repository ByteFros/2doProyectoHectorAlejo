import { useRef, useState, useEffect } from "react";
import { useTripNotes } from "../../../../hooks/useTripNotes";
import styles from "./notes-section.module.scss";

interface Props {
    tripId: number;
}

interface SwipeState {
    noteId: number | null;
    startX: number;
    currentX: number;
    isDragging: boolean;
}

export default function NotesSection({ tripId }: Props) {
    const { notes, createNote, deleteNote } = useTripNotes(tripId);
    const textareaRef = useRef<HTMLTextAreaElement | null>(null);
    const notesListRef = useRef<HTMLUListElement | null>(null);
    
    // Estado para controlar el deslizamiento
    const [swipeState, setSwipeState] = useState<SwipeState>({
        noteId: null,
        startX: 0,
        currentX: 0,
        isDragging: false
    });
    
    // Referencia para almacenar los elementos de notas
    const noteRefs = useRef<{[key: number]: HTMLLIElement | null}>({});

    // Efecto para desplazar al final de la lista cuando se agrega una nueva nota
    useEffect(() => {
        if (notesListRef.current) {
            notesListRef.current.scrollTop = 0; // Scroll al principio (notas más recientes)
        }
    }, [notes.length]);

    const handleNoteChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const value = e.target.value;
        if (value.endsWith("\n")) {
            const newNote = value.trim();
            if (newNote.length > 0) {
                createNote(newNote);
                if (textareaRef.current) textareaRef.current.value = "";
            }
        }
    };

    // Manejadores para el deslizamiento
    const handleTouchStart = (e: React.MouseEvent | React.TouchEvent, noteId: number) => {
        const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
        
        setSwipeState({
            noteId,
            startX: clientX,
            currentX: clientX,
            isDragging: true
        });
    };

    const handleTouchMove = (e: React.MouseEvent | React.TouchEvent) => {
        if (!swipeState.isDragging) return;
        
        const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
        
        setSwipeState(prev => ({
            ...prev,
            currentX: clientX
        }));
        
        if (swipeState.noteId !== null && noteRefs.current[swipeState.noteId]) {
            const diff = clientX - swipeState.startX;
            // Limitar el deslizamiento a la izquierda
            const translateX = Math.min(0, diff);
            
            // Aplicar transformación
            const noteElement = noteRefs.current[swipeState.noteId];
            if (noteElement) {
                noteElement.style.transform = `translateX(${translateX}px)`;
                
                // Cambiar opacidad del fondo de eliminación según el deslizamiento
                const opacity = Math.min(1, Math.abs(translateX) / 100);
                const deleteBackground = noteElement.querySelector(`.${styles.deleteBackground}`);
                if (deleteBackground) {
                    (deleteBackground as HTMLElement).style.opacity = opacity.toString();
                }
            }
        }
    };

    const handleTouchEnd = () => {
        if (!swipeState.isDragging || swipeState.noteId === null) {
            setSwipeState({
                noteId: null,
                startX: 0,
                currentX: 0,
                isDragging: false
            });
            return;
        }

        const diff = swipeState.currentX - swipeState.startX;
        const noteElement = noteRefs.current[swipeState.noteId];
        
        // Si se ha deslizado suficientemente a la izquierda, eliminar la nota
        if (diff < -100 && noteElement) {
            // Efecto de deslizamiento completo antes de eliminar
            noteElement.style.transform = 'translateX(-100%)';
            noteElement.style.transition = 'transform 0.3s ease';
            
            // Esperamos a que termine la animación para eliminar la nota
            setTimeout(() => {
                deleteNote(swipeState.noteId as number);
            }, 300);
        } else if (noteElement) {
            // Volver a la posición inicial
            noteElement.style.transform = 'translateX(0)';
            noteElement.style.transition = 'transform 0.3s ease';
        }
        
        // Resetear el estado después de un tiempo para eliminar la transición
        setTimeout(() => {
            if (noteElement) {
                noteElement.style.transition = '';
            }
            
            setSwipeState({
                noteId: null,
                startX: 0,
                currentX: 0,
                isDragging: false
            });
        }, 300);
    };

    // Limpiar event listeners cuando el componente se desmonta
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (swipeState.isDragging) {
                handleTouchMove(e as unknown as React.MouseEvent);
            }
        };
        
        const handleMouseUp = () => {
            if (swipeState.isDragging) {
                handleTouchEnd();
            }
        };
        
        // Agregar event listeners globales para manejar el deslizamiento
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [swipeState]);

    // Comprobar si hay notas para mostrar
    const hasNotes = notes.length > 0;

    return (
        <div className={styles.notesSection}>
            <h4>Notas</h4>
            <textarea
                ref={textareaRef}
                onChange={handleNoteChange}
                placeholder="Escribe una nota y presiona Enter..."
            />
            <ul ref={notesListRef} className={hasNotes ? '' : styles.emptyList}>
                {hasNotes ? (
                    notes.map((note) => (
                        <li 
                            key={note.id} 
                            className={styles.noteItem}
                            ref={el => noteRefs.current[note.id] = el}
                            onMouseDown={(e) => handleTouchStart(e, note.id)}
                            onTouchStart={(e) => handleTouchStart(e, note.id)}
                            onTouchMove={handleTouchMove}
                            onTouchEnd={handleTouchEnd}
                        >
                            <div className={styles.deleteBackground}>
                                <span>Eliminar</span>
                            </div>
                            <div className={styles.noteContent}>
                                <span>{note.contenido}</span>
                            </div>
                        </li>
                    ))
                ) : (
                    <li className={styles.emptyNoteItem}>
                        <div className={styles.noteContent}>
                            <span className={styles.emptyMessage}>No hay notas. Escribe algo y presiona Enter.</span>
                        </div>
                    </li>
                )}
            </ul>
        </div>
    );
}
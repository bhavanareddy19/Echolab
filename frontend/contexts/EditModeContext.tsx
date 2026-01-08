'use client';
import { createContext, useContext, useState } from 'react';

type EditModeContextType = {
  isEditing: boolean;
  setIsEditing: (editing: boolean) => void;
};

const EditModeContext = createContext<EditModeContextType | undefined>(
  undefined
);

export function EditModeProvider({ children }: { children: React.ReactNode }) {
  const [isEditing, setIsEditing] = useState(false);
  return (
    <EditModeContext.Provider value={{ isEditing, setIsEditing }}>
      {children}
    </EditModeContext.Provider>
  );
}

export function useEditMode() {
  const ctx = useContext(EditModeContext);
  if (!ctx) throw new Error('useEditMode must be used inside EditModeProvider');
  return ctx;
}

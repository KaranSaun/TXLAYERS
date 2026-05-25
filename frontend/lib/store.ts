import { create } from 'zustand';
import { Design, User } from './types';

interface AppStore {
  user: User | null;
  setUser: (user: User | null) => void;
  
  currentDesign: Design | null;
  setDesign: (design: Design | null) => void;
  
  visibleLayers: Set<string>;
  toggleLayer: (id: string) => void;
  setVisibleLayers: (layers: Set<string>) => void;
  showAllLayers: () => void;
  hideAllLayers: () => void;
  
  isAuthenticated: () => boolean;
  logout: () => void;
}

export const useStore = create<AppStore>((set, get) => ({
  user: null,
  setUser: (user) => set({ user }),
  
  currentDesign: null,
  setDesign: (design) => {
    set({ currentDesign: design });
    if (design && design.layers) {
      const layerIds = new Set(design.layers.map(l => l.id));
      set({ visibleLayers: layerIds });
    }
  },
  
  visibleLayers: new Set(),
  toggleLayer: (id) => set((state) => {
    const newVisible = new Set(state.visibleLayers);
    if (newVisible.has(id)) {
      newVisible.delete(id);
    } else {
      newVisible.add(id);
    }
    return { visibleLayers: newVisible };
  }),
  
  setVisibleLayers: (layers) => set({ visibleLayers: layers }),
  
  showAllLayers: () => set((state) => {
    if (state.currentDesign && state.currentDesign.layers) {
      const allIds = new Set(state.currentDesign.layers.map(l => l.id));
      return { visibleLayers: allIds };
    }
    return state;
  }),
  
  hideAllLayers: () => set({ visibleLayers: new Set() }),
  
  isAuthenticated: () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    return !!token;
  },
  
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
    set({ user: null, currentDesign: null, visibleLayers: new Set() });
  },
}));

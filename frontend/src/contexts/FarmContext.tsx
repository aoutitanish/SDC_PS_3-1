import React, { createContext, useContext, useState, useEffect } from 'react';
import { FarmProfile } from '../types';
import { api } from '../services/api';

interface FarmContextType {
  farm: FarmProfile;
  setFarm: (profile: FarmProfile) => Promise<void>;
  loading: boolean;
}

const defaultProfile: FarmProfile = {
  farm_name: 'Kurnool Farm',
  state: 'Andhra Pradesh',
  district: 'Kurnool',
  soil_type: 'Black Soil (Regur/Vertisol)',
  farm_size_acres: 5.0,
  irrigation_type: 'Drip Irrigation & Borewell',
  primary_crops: ['Arhar/Tur (Pigeon Pea)', 'Cotton', 'Chilli'],
  preferred_language: 'en'
};

const FarmContext = createContext<FarmContextType | undefined>(undefined);

export const FarmProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [farm, setFarmState] = useState<FarmProfile>(() => {
    const cached = localStorage.getItem('krishi_farm_profile');
    return cached ? JSON.parse(cached) : defaultProfile;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getFarmProfile('guest')
      .then((data) => {
        if (data) {
          setFarmState(data);
          localStorage.setItem('krishi_farm_profile', JSON.stringify(data));
        }
      })
      .catch((err) => console.warn('Using local farm profile:', err));
  }, []);

  const setFarm = async (profile: FarmProfile) => {
    setLoading(true);
    try {
      setFarmState(profile);
      localStorage.setItem('krishi_farm_profile', JSON.stringify(profile));
      await api.saveFarmProfile(profile, 'guest');
    } catch (err) {
      console.error('Error saving farm profile:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <FarmContext.Provider value={{ farm, setFarm, loading }}>
      {children}
    </FarmContext.Provider>
  );
};

export const useFarm = () => {
  const context = useContext(FarmContext);
  if (!context) {
    throw new Error('useFarm must be used within a FarmProvider');
  }
  return context;
};

import { useState, useCallback, useEffect } from 'react';
import type { ProfileData } from '../types';
import * as api from '../api/client';

export function useProfile() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getMyProfile();
      setProfile(data);
    } catch (err) {
      console.error('Failed to fetch profile:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const refreshProfile = useCallback(() => {
    fetchProfile();
  }, [fetchProfile]);

  return { profile, loading, refreshProfile };
}

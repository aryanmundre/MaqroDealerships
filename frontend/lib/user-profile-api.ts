import type { UserProfile } from './supabase';
import { getAuthenticatedApi } from './api-client';

export interface UserProfileCreate {
  dealership_id?: string | null
  full_name: string
  phone?: string | null
  role?: string
  timezone?: string
}
export type UserProfileUpdate = Partial<Omit<UserProfileCreate, "dealership_id">>

export async function createUserProfile(
  payload: UserProfileCreate
): Promise<UserProfile> {
  const api = await getAuthenticatedApi();
  return api.post<UserProfile>('/user_profiles', payload);
}

export async function getMyProfile(): Promise<UserProfile> {
  const api = await getAuthenticatedApi()
  return api.get<UserProfile>("/user-profiles/me")
}

export async function updateMyProfile(
  payload: Partial<Omit<UserProfile, "id" | "user_id" | "dealership_id" | "created_at" | "updated_at">>
): Promise<UserProfile> {
  const api = await getAuthenticatedApi()
  return api.put<UserProfile>("/user-profiles/me", payload)
}

export async function getDealershipProfile(): Promise<UserProfile[]> {
  const api = await getAuthenticatedApi();
  return api.get<UserProfile[]>('/user_profiles/dealership');
}
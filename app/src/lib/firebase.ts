/**
 * Firebase Configuration & Auth Utilities
 * EdgeIQ uses Firebase Auth for frontend authentication
 */

import { initializeApp } from "firebase/app";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  updateProfile as firebaseUpdateProfile,
  updatePassword,
  signOut,
  onAuthStateChanged,
  type User,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

export function getAuthToken(): string | null {
  return localStorage.getItem("edgeiq_firebase_token");
}

export function setAuthToken(token: string | null): void {
  if (token) {
    localStorage.setItem("edgeiq_firebase_token", token);
  } else {
    localStorage.removeItem("edgeiq_firebase_token");
  }
}

export async function refreshToken(): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  const token = await user.getIdToken(true);
  setAuthToken(token);
  return token;
}

export async function registerWithEmail(email: string, password: string, displayName: string): Promise<User> {
  const result = await createUserWithEmailAndPassword(auth, email, password);
  await firebaseUpdateProfile(result.user, { displayName });
  const token = await result.user.getIdToken();
  setAuthToken(token);
  return result.user;
}

export async function loginWithEmail(email: string, password: string): Promise<User> {
  const result = await signInWithEmailAndPassword(auth, email, password);
  const token = await result.user.getIdToken();
  setAuthToken(token);
  return result.user;
}

export async function logoutFirebase(): Promise<void> {
  await signOut(auth);
  setAuthToken(null);
}

export async function updateUserProfile(displayName: string): Promise<void> {
  const user = auth.currentUser;
  if (!user) throw new Error("No authenticated user");
  await firebaseUpdateProfile(user, { displayName });
}

export async function updateUserPassword(newPassword: string): Promise<void> {
  const user = auth.currentUser;
  if (!user) throw new Error("No authenticated user");
  await updatePassword(user, newPassword);
}

export function initAuthListener(callback: (user: User | null) => void): () => void {
  return onAuthStateChanged(auth, async (user: User | null) => {
    if (user) {
      const token = await user.getIdToken();
      setAuthToken(token);
    } else {
      setAuthToken(null);
    }
    callback(user);
  });
}
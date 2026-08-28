"use client";

// MVP : tokens en localStorage (simple, mais vulnérable en cas de XSS).
// À revoir en V2 (cookie httpOnly + refresh côté serveur) avant une mise en
// production à plus grande échelle.
const ACCESS_KEY = "sgt_access_token";
const REFRESH_KEY = "sgt_refresh_token";

export function storeTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isLoggedIn(): boolean {
  return getAccessToken() !== null;
}

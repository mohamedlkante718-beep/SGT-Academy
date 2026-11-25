const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export type Category = {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
};

export type Instructor = {
  id: string;
  full_name: string;
  headline: string;
  is_verified: boolean;
};

export type CourseListItem = {
  slug: string;
  title: string;
  short_description: string;
  cover_image: string | null;
  level: "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
  duration_hours: number;
  price: string;
  promo_price: string | null;
  currency: string;
  certificate_available: boolean;
  categories: Category[];
  instructors: Instructor[];
  modules_count: number;
  students_count: number;
};

export type Lesson = {
  id: string;
  title: string;
  order: number;
  duration_seconds: number;
  is_preview: boolean;
};

export type Module = {
  id: string;
  title: string;
  description: string;
  order: number;
  lessons: Lesson[];
};

export type CourseDetail = {
  slug: string;
  title: string;
  short_description: string;
  description: string;
  objectives: string[];
  skills_acquired: string[];
  prerequisites: string[];
  cover_image: string | null;
  level: "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
  duration_hours: number;
  price: string;
  promo_price: string | null;
  currency: string;
  certificate_available: boolean;
  categories: Category[];
  instructors: Instructor[];
  modules: Module[];
  students_count: number;
  seo_title: string;
  seo_description: string;
};

type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type CourseFilters = {
  category?: string;
  level?: string;
  certificate_available?: boolean;
  min_price?: number;
  max_price?: number;
  search?: string;
  ordering?: string;
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const isRead = !init?.method || init.method === "GET";
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    // Le catalogue public change rarement dans la journée : on rafraîchit toutes les 60s.
    // Les écritures (POST/PATCH) ne doivent jamais être mises en cache.
    ...(isRead ? { next: { revalidate: 60 } } : { cache: "no-store" as const }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body);
  }
  return response.json();
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`Erreur API (${status})`);
    this.status = status;
    this.body = body;
  }
}

export function getCourses(filters: CourseFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const query = params.toString();
  return apiFetch<PaginatedResponse<CourseListItem>>(`/courses/${query ? `?${query}` : ""}`);
}

export function getCourseBySlug(slug: string) {
  return apiFetch<CourseDetail>(`/courses/${slug}/`);
}

export type CertificateVerification = {
  valid: boolean;
  code: string;
  learner_name?: string;
  course_title?: string;
  issued_at?: string;
};

export function verifyCertificate(code: string) {
  return apiFetch<CertificateVerification>(`/certificates/verify/${encodeURIComponent(code)}/`);
}

export type AuthTokens = { access: string; refresh: string };

export async function login(email: string, password: string): Promise<AuthTokens> {
  return apiFetch<AuthTokens>("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export type RegisterPayload = {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  country?: string;
  password: string;
  password_confirm: string;
};

export function register(payload: RegisterPayload) {
  return apiFetch("/auth/register/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function verifyEmail(email: string, code: string) {
  return apiFetch("/auth/verify-email/", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

export function resendVerificationCode(email: string) {
  return apiFetch("/auth/resend-verification/", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function purchaseCourse(slug: string, accessToken: string) {
  return apiFetch<{ reference: string; status: string; amount: string; currency: string }>(
    `/courses/${slug}/purchase/`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify({ method: "MANUAL" }),
    }
  );
}

// Upload de fichier (multipart) : ne passe pas par apiFetch, qui force
// Content-Type: application/json — le navigateur doit fixer lui-même le
// boundary multipart quand le corps est un FormData.
export async function submitManualProof(
  paymentReference: string,
  accessToken: string,
  transactionReference: string,
  proof?: File
) {
  const formData = new FormData();
  formData.set("reference", transactionReference);
  if (proof) formData.set("proof", proof);

  const response = await fetch(`${API_BASE_URL}/payments/${paymentReference}/proof/`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: formData,
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, body);
  }
  return response.json();
}

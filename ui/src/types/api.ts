// Types generated from OpenAPI spec — source of truth
export type Role = "STUDENT" | "TEACHER" | "DEAN" | "ADMIN";
export type ApplicationStatus =
  | "PENDING"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "ENROLLED";

export interface UserPublic {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}
export interface RegisterResponse extends UserPublic {}

export interface LoginRequest {
  email: string;
  password: string;
}
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in: number;
}
export interface RefreshRequest {
  refresh_token: string;
}
export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}
export interface MessageResponse {
  status?: string;
}

export interface ApplicationCreate {
  program_code: string;
  intake_term: string;
  statement?: string | null;
}
export interface ApplicationRead {
  id: string;
  applicant_user_id: string;
  status: string;
  program_code: string;
  intake_term: string;
  statement: string | null;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  decision_notes: string | null;
  resulting_student_id: string | null;
  created_at: string;
  updated_at: string;
}
export interface ApplicationStatusPatch {
  status: ApplicationStatus;
  notes?: string | null;
}

export interface StudentRead {
  id: string;
  user_id: string;
  student_number: string;
  enrollment_status: string;
  academic_group: string | null;
  specialty: string | null;
  enrollment_date: string | null;
  academic_status: string | null;
  created_at: string;
  updated_at: string;
}
export interface StudentProfileResponse {
  student: StudentRead;
  gpa: string;
}
export interface StudentPatch {
  academic_group?: string | null;
  specialty?: string | null;
  enrollment_date?: string | null;
  academic_status?: string | null;
  enrollment_status?: string | null;
}

export interface TeacherBrief {
  id: string;
  employee_id: string;
  department: string | null;
}
export interface CourseRead {
  id: string;
  code: string;
  title?: string;
  description?: string;
  credits: string;
  teacher_id: string;
  created_at: string;
  updated_at: string;
  teacher?: TeacherBrief | null;
}
export interface CourseCreate {
  code: string;
  title?: string;
  credits: number | string;
  teacher_id: string;
}
export interface CoursePatch {
  credits?: number | string | null;
  teacher_id?: string | null;
}
export interface CourseStudentEnroll {
  student_id: string;
}

export interface GradeRead {
  id: string;
  student_id: string;
  course_id: string;
  score: string;
  letter_grade: string | null;
  recorded_at: string;
  created_at: string;
  updated_at: string;
}
export interface GradeCreate {
  student_id: string;
  course_id: string;
  score: number | string;
  letter_grade?: string | null;
}
export interface GradePatch {
  score: number | string;
  letter_grade?: string | null;
  reason?: string | null;
}

export interface AdminRoleUpdate {
  role: Role;
}

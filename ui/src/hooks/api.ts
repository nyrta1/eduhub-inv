import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import type {
  AdminRoleUpdate,
  ApplicationCreate,
  ApplicationRead,
  ApplicationStatusPatch,
  ChangePasswordRequest,
  CourseCreate,
  CoursePatch,
  CourseRead,
  CourseStudentEnroll,
  GradeCreate,
  GradePatch,
  GradeRead,
  LoginRequest,
  MessageResponse,
  RegisterRequest,
  RegisterResponse,
  StudentPatch,
  StudentProfileResponse,
  StudentRead,
  TokenResponse,
  UserPublic,
} from "@/types/api";

// ---------- AUTH ----------
export function useRegister() {
  return useMutation({
    mutationFn: async (body: RegisterRequest) =>
      (await api.post<RegisterResponse>("/api/v1/auth/register", body)).data,
  });
}

export function useLogin() {
  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const { data } = await api.post<TokenResponse>(
        "/api/v1/auth/login",
        body,
      );
      useAuthStore
        .getState()
        .setTokens(data.access_token, data.refresh_token);
      const me = await api.get<UserPublic>("/api/v1/auth/me");
      useAuthStore.getState().setUser(me.data);
      return me.data;
    },
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      try {
        await api.post<MessageResponse>("/api/v1/auth/logout");
      } catch {}
      useAuthStore.getState().clear();
      qc.clear();
    },
  });
}

export function useLogoutAll() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post<MessageResponse>("/api/v1/auth/logout-all");
      useAuthStore.getState().clear();
      qc.clear();
    },
  });
}

export function useMe(enabled = true) {
  return useQuery({
    queryKey: ["me"],
    enabled,
    queryFn: async () => (await api.get<UserPublic>("/api/v1/auth/me")).data,
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (body: ChangePasswordRequest) =>
      (await api.post<MessageResponse>("/api/v1/auth/change-password", body))
        .data,
  });
}

// ---------- APPLICATIONS ----------
export function useApplications() {
  return useQuery({
    queryKey: ["applications"],
    queryFn: async () =>
      (await api.get<ApplicationRead[]>("/api/v1/applications")).data,
  });
}
export function useMyApplications() {
  return useQuery({
    queryKey: ["applications", "my"],
    queryFn: async () =>
      (await api.get<ApplicationRead[]>("/api/v1/applications/my")).data,
  });
}
export function useApplication(id: string) {
  return useQuery({
    queryKey: ["applications", id],
    enabled: !!id,
    queryFn: async () =>
      (await api.get<ApplicationRead>(`/api/v1/applications/${id}`)).data,
  });
}
export function useCreateApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: ApplicationCreate) =>
      (await api.post<ApplicationRead>("/api/v1/applications", body)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}
export function useReviewApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { id: string; body: ApplicationStatusPatch }) =>
      (
        await api.patch<ApplicationRead>(
          `/api/v1/applications/${vars.id}/status`,
          vars.body,
        )
      ).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

// ---------- STUDENTS ----------
export function useStudents() {
  return useQuery({
    queryKey: ["students"],
    queryFn: async () =>
      (await api.get<StudentRead[]>("/api/v1/students")).data,
  });
}
export function useMyStudent() {
  return useQuery({
    queryKey: ["students", "me"],
    queryFn: async () =>
      (await api.get<StudentProfileResponse>("/api/v1/students/me")).data,
  });
}
export function useStudent(id: string) {
  return useQuery({
    queryKey: ["students", id],
    enabled: !!id,
    queryFn: async () =>
      (await api.get<StudentProfileResponse>(`/api/v1/students/${id}`)).data,
  });
}
export function useUpdateStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { id: string; body: StudentPatch }) =>
      (await api.patch<StudentRead>(`/api/v1/students/${vars.id}`, vars.body))
        .data,
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ["students"] });
      qc.invalidateQueries({ queryKey: ["students", v.id] });
    },
  });
}

// ---------- COURSES ----------
export function useCourses() {
  return useQuery({
    queryKey: ["courses"],
    queryFn: async () =>
      (await api.get<CourseRead[]>("/api/v1/courses")).data,
  });
}
export function useCourse(id: string) {
  return useQuery({
    queryKey: ["courses", id],
    enabled: !!id,
    queryFn: async () =>
      (await api.get<CourseRead>(`/api/v1/courses/${id}`)).data,
  });
}
export function useCreateCourse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: CourseCreate) =>
      (await api.post<CourseRead>("/api/v1/courses", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["courses"] }),
  });
}
export function useUpdateCourse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { id: string; body: CoursePatch }) =>
      (await api.patch<CourseRead>(`/api/v1/courses/${vars.id}`, vars.body))
        .data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["courses"] }),
  });
}
export function useEnrollStudent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { courseId: string; body: CourseStudentEnroll }) =>
      (
        await api.post<void>(
          `/api/v1/courses/${vars.courseId}/students`,
          vars.body,
        )
      ).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["courses"] }),
  });
}

// ---------- GRADES ----------
export function useMyGrades() {
  return useQuery({
    queryKey: ["grades", "my"],
    queryFn: async () =>
      (await api.get<GradeRead[]>("/api/v1/grades/my")).data,
  });
}
export function useGradesForStudent(id: string) {
  return useQuery({
    queryKey: ["grades", "student", id],
    enabled: !!id,
    queryFn: async () =>
      (await api.get<GradeRead[]>(`/api/v1/grades/student/${id}`)).data,
  });
}
export function useGradesForCourse(id: string) {
  return useQuery({
    queryKey: ["grades", "course", id],
    enabled: !!id,
    queryFn: async () =>
      (await api.get<GradeRead[]>(`/api/v1/grades/course/${id}`)).data,
  });
}
export function useCreateGrade() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: GradeCreate) =>
      (await api.post<GradeRead>("/api/v1/grades", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["grades"] }),
  });
}
export function useUpdateGrade() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { id: string; body: GradePatch }) =>
      (await api.patch<GradeRead>(`/api/v1/grades/${vars.id}`, vars.body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["grades"] }),
  });
}

// ---------- ADMIN ----------
export function useAssignRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { userId: string; body: AdminRoleUpdate }) =>
      (
        await api.patch<UserPublic>(
          `/api/v1/users/${vars.userId}/role`,
          vars.body,
        )
      ).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

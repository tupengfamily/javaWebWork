import request from '@/utils/request'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  expiresIn: number
  user: { id: number; username: string; role: string }
}

export const login = (data: LoginRequest) =>
  request.post<any, LoginResponse>('/auth/login', data)

export const logout = () => request.post('/auth/logout')

export const fetchMe = () => request.get('/auth/me')

import type { UserRole } from '../types/api'

export function roleLabel(role: UserRole | string | undefined): string {
  switch (role) {
    case 'admin':
      return '管理员'
    case 'it_support':
      return 'IT 支持'
    case 'employee':
      return '普通员工'
    default:
      return role || '未知角色'
  }
}

/** User-facing Chinese labels for catalog services (keeps API codes unchanged). */

const SERVICE_DISPLAY: Record<string, { name: string; hint: string }> = {
  CHECKOUT_API: {
    name: '收银台 / 下单支付',
    hint: '无法下单、支付超时、收银台报错等',
  },
  AUTH_SERVICE: {
    name: '登录与账号认证',
    hint: '登录失败、会话异常、账号无法使用等',
  },
  ORDER_WORKER: {
    name: '订单后台处理',
    hint: '订单积压、异步任务卡住、处理延迟等',
  },
  GENERAL_IT: {
    name: '其他类型',
    hint: 'VPN、设备报修、软件安装等无法归入上述系统时选此项',
  },
}


export function serviceDisplayName(code: string, fallbackName?: string | null): string {
  const mapped = SERVICE_DISPLAY[code]
  if (mapped) return mapped.name
  return (fallbackName || code || '未知服务').trim()
}

export function serviceHint(code: string): string {
  return SERVICE_DISPLAY[code]?.hint ?? ''
}

export function serviceOptionLabel(code: string, fallbackName?: string | null): string {
  const name = serviceDisplayName(code, fallbackName)
  const hint = serviceHint(code)
  return hint ? `${name}（${hint}）` : name
}

export function healthStatusLabel(status: string): string {
  switch (status) {
    case 'HEALTHY':
      return '正常'
    case 'DEGRADED':
      return '异常 / 降级'
    case 'DOWN':
      return '不可用'
    default:
      return status || '未知'
  }
}

export function healthStatusColor(status: string): string {
  if (status === 'HEALTHY') return 'success'
  if (status === 'DEGRADED') return 'warning'
  if (status === 'DOWN') return 'error'
  return 'default'
}

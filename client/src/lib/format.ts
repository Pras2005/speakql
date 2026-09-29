export function formatDate(value?: string | null) {
  if (!value) {
    return 'No timestamp';
  }
  return new Date(value).toLocaleString();
}

export function prettyJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

export function statusClass(status?: string | null) {
  switch (status) {
    case 'ok':
    case 'healthy':
      return 'status-ok';
    case 'degraded':
      return 'status-degraded';
    case 'offline':
    case 'error':
      return 'status-offline';
    default:
      return 'status-unknown';
  }
}

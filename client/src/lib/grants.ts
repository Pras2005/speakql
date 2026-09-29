import type { AccessLevel, CurrentUser, Database } from '@/lib/types';

export const GRANT_RANK: Record<AccessLevel, number> = {
  discover: 1,
  query: 2,
  export: 3,
  manage: 4,
};

export function getEffectiveAccessLevel(database: Database | null | undefined, user?: CurrentUser | null) {
  if (!database) {
    return null;
  }
  if (user?.role === 'admin') {
    return 'manage' as AccessLevel;
  }
  return database.access_level ?? null;
}

export function canAccess(level: AccessLevel | null | undefined, required: AccessLevel) {
  if (!level) {
    return false;
  }
  return GRANT_RANK[level] >= GRANT_RANK[required];
}

export function grantTone(level: AccessLevel | null | undefined) {
  switch (level) {
    case 'discover':
      return 'pill-discover';
    case 'query':
      return 'pill-query';
    case 'export':
      return 'pill-export';
    case 'manage':
      return 'pill-manage';
    default:
      return 'pill-neutral';
  }
}

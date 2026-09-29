import { useQuery } from '@tanstack/react-query';

import { authApi } from '@/api/auth';
import { tenancyApi } from '@/api/tenancy';
import { hasToken } from '@/lib/auth';
import { useSessionStore } from '@/store/session';

export function useSessionBootstrap() {
  const setCurrentUser = useSessionStore((state) => state.setCurrentUser);
  const setMemberships = useSessionStore((state) => state.setMemberships);

  return useQuery({
    queryKey: ['session-bootstrap'],
    enabled: hasToken(),
    queryFn: async () => {
      const [userResponse, membershipsResponse] = await Promise.all([
        authApi.me(),
        tenancyApi.memberships(),
      ]);

      setCurrentUser(userResponse.data);
      setMemberships(membershipsResponse.data);

      return {
        user: userResponse.data,
        memberships: membershipsResponse.data,
      };
    },
  });
}

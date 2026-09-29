const messages = {
  discover: "You don't have schema discovery access for this database.",
  query: "You don't have query access for this database.",
  export: "You don't have export access for this database.",
  manage: 'You need manage access for this database.',
};

export function PermissionBanner({ action }: { action: keyof typeof messages }) {
  return <div className="permission-banner">{messages[action]}</div>;
}

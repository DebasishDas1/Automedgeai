export const getDomainUrl = (subdomain?: string) => {
  const root = process.env.NEXT_PUBLIC_ROOT_DOMAIN;

  if (!root) return "/";

  if (!subdomain) return `http://${root}`;
  return `http://${subdomain}.${root}`;
};

export const getCurrentSubdomain = () => {
  if (typeof window === "undefined") return null;

  const host = window.location.hostname; // demo-hvac.localhost
  const parts = host.split(".");

  return parts.length > 1 ? parts[0] : null;
};

export const useDomainNavigation = () => {
  const goTo = (subdomain?: string) => {
    const target = getDomainUrl(subdomain);
    if (window.location.href === target) return; // no reload
    window.location.href = target;
  };

  const goToDemo = (industry: string) => {
    goTo(`demo-${industry}`);
  };

  const getCurrentDomain = () => {
    return getCurrentSubdomain();
  };

  const goHome = () => {
    goTo();
  };

  return { goTo, goToDemo, goHome, getCurrentDomain };
};
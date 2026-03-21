const isLocalhost = (host: string) =>
  host.includes("localhost") || host.includes("127.0.0.1");


export const getDomainUrl = (subdomain?: string) => {
  if (typeof window === "undefined") return "/";

  const protocol = window.location.protocol; // auto http/https
  const root = process.env.NEXT_PUBLIC_ROOT_DOMAIN;

  if (!root) return "/";

  // Local dev → use path instead of subdomain
  if (isLocalhost(window.location.hostname)) {
    if (!subdomain) return `${protocol}//${root}`;
    return `${protocol}//${root}/${subdomain}`;
  }

  // Production → real subdomains
  if (!subdomain) return `${protocol}//${root}`;
  return `${protocol}//${subdomain}.${root}`;
};



export const getCurrentSubdomain = () => {
  if (typeof window === "undefined") return null;

  const host = window.location.hostname;

  if (isLocalhost(host)) return null;

  const parts = host.split(".");

  // ignore www
  if (parts[0] === "www") return null;

  return parts.length > 2 ? parts[0] : null;
};



import { useRouter } from "next/navigation";

export const useDomainNavigation = () => {
  const router = useRouter();

  const getTargetInfo = (subdomain?: string) => {
    if (typeof window === "undefined") return { url: "/", isExternal: false };

    const host = window.location.hostname;
    const protocol = window.location.protocol;
    const root = process.env.NEXT_PUBLIC_ROOT_DOMAIN;

    if (!root) return { url: "/", isExternal: false };

    // LOCALHOST logic (dev)
    if (isLocalhost(host)) {
      const path = subdomain ? `/${subdomain}` : "/";
      return { url: path, isExternal: false };
    }

    // PRODUCTION logic
    const currentSubdomain = getCurrentSubdomain();

    // If already on the target subdomain, it's internal navigation
    if (currentSubdomain === (subdomain || null)) {
      return { url: "/", isExternal: false };
    }

    // If navigating to root or another subdomain
    const url = subdomain 
      ? `${protocol}//${subdomain}.${root}`
      : `${protocol}//${root}`;

    return { url, isExternal: true };
  };

  const goTo = (subdomain?: string) => {
    const { url, isExternal } = getTargetInfo(subdomain);

    if (isExternal) {
      window.location.assign(url);
    } else {
      router.push(url);
    }
  };

  const goToDemo = (industry: string) => {
    goTo(`demo-${industry}`);
  };

  const goHome = () => {
    goTo();
  };

  const getCurrentDomain = () => {
    return getCurrentSubdomain();
  };

  return { goTo, goToDemo, goHome, getCurrentDomain };
};
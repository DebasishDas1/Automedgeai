const isLocalhost = (host: string) =>
  host.includes("localhost") || host.includes("127.0.0.1");

const isValidSubdomain = (value?: string): value is string =>
  typeof value === "string" &&
  /^[a-z0-9-]+$/.test(value) &&
  !value.startsWith("-") &&
  !value.endsWith("-");

const isPath = (value?: string): value is string =>
  typeof value === "string" && value.startsWith("/");

// ----------------------
// DOMAIN URL GENERATOR
// ----------------------
export const getDomainUrl = (target?: string) => {
  if (typeof window === "undefined") return "/";

  const protocol = window.location.protocol;
  const host = window.location.hostname;
  const root = process.env.NEXT_PUBLIC_ROOT_DOMAIN;

  if (!root) return "/";

  // 👉 If it's a path → return directly
  if (isPath(target)) return target;

  const subdomain = isValidSubdomain(target) ? target : undefined;

  // 👉 Localhost → fallback to path-based routing
  if (isLocalhost(host)) {
    return subdomain ? `/${subdomain}` : "/";
  }

  // 👉 Production → real subdomains
  return subdomain
    ? `${protocol}//${subdomain}.${root}`
    : `${protocol}//${root}`;
};

// ----------------------
// CURRENT SUBDOMAIN
// ----------------------
export const getCurrentSubdomain = () => {
  if (typeof window === "undefined") return null;

  const host = window.location.hostname;

  if (isLocalhost(host)) return null;

  const parts = host.split(".");

  if (parts[0] === "www") return null;

  return parts.length > 2 ? parts[0] : null;
};

// ----------------------
// HOOK
// ----------------------
import { useRouter } from "next/navigation";

export const useDomainNavigation = () => {
  const router = useRouter();

  const getTargetInfo = (target?: string) => {
    if (typeof window === "undefined") {
      return { url: "/", isExternal: false };
    }

    const protocol = window.location.protocol;
    const host = window.location.hostname;
    const root = process.env.NEXT_PUBLIC_ROOT_DOMAIN;

    if (!root) return { url: "/", isExternal: false };

    // 👉 PATH navigation (highest priority)
    if (isPath(target)) {
      return { url: target, isExternal: false };
    }

    const subdomain = isValidSubdomain(target) ? target : undefined;

    // 👉 LOCALHOST (dev)
    if (isLocalhost(host)) {
      return {
        url: subdomain ? `/${subdomain}` : "/",
        isExternal: false,
      };
    }

    // 👉 PRODUCTION
    const currentSubdomain = getCurrentSubdomain();

    if (currentSubdomain === (subdomain || null)) {
      return { url: "/", isExternal: false };
    }

    const url = subdomain
      ? `${protocol}//${subdomain}.${root}`
      : `${protocol}//${root}`;

    return { url, isExternal: true };
  };

  // ----------------------
  // NAVIGATION
  // ----------------------
  const goTo = (target?: string) => {
    const { url, isExternal } = getTargetInfo(target);

    if (isExternal) {
      window.location.assign(url);
    } else {
      router.push(url);
    }
  };

  const goToDemo = (industry: string) => {
    const safe = industry
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, "")
      .replace(/^-+|-+$/g, "");

    if (!safe) return goHome();

    goTo(`demo-${safe}`);
  };

  const goHome = () => goTo();

  const getCurrentDomain = () => getCurrentSubdomain();

  return { goTo, goToDemo, goHome, getCurrentDomain };
};
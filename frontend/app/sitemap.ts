import { MetadataRoute } from 'next'
import { headers } from 'next/headers'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Gracefully handle headers() depending on Next.js version (sync vs async)
  const headersList = headers()
  // @ts-expect-error - Handling Next.js 14/15 breaking changes gracefully
  let host = headersList.get ? headersList.get('host') : (await headersList).get('host')
  
  host = host || 'automedge.com'
  
  const protocol = host.includes('localhost') || host.startsWith('192.168.') || host.startsWith('127.0.0.1') ? 'http' : 'https'
  const baseUrl = `${protocol}://${host}`

  // Check if we are on the main domain or a subdomain
  const isMainDomain = 
    host === 'automedge.com' || 
    host === 'www.automedge.com' || 
    host.startsWith('localhost') || 
    host.startsWith('192.168.') || 
    host.startsWith('127.0.0.1')

  // Main domain sitemap: Include all pages
  if (isMainDomain) {
    const routes = [
      '',
      '/demo-hvac',
      '/demo-pest-control',
      '/demo-plumbing',
      '/demo-roofing',
    ]

    return routes.map((route) => ({
      url: `${baseUrl}${route}`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: route === '' ? 1 : 0.8,
    }))
  }

  // Subdomain sitemap: The subdomain maps exclusively to a specific demo folder,
  // so from the public's perspective, the "root" of the subdomain is the page itself.
  return [
    {
      url: `${baseUrl}/`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 1,
    }
  ]
}

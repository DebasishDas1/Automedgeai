import { Vertical } from '../types';

export const VERTICALS: Record<string, Vertical> = {
    hvac: {
        slug: 'hvac',
        label: 'HVAC',
        pain: 'Missed calls while on the job',
        fix: 'Auto-SMS within 60s of any missed call',
        demoLead: {
            name: 'Mike Johnson',
            issue: 'AC not cooling · 3-bed home',
            city: 'Dallas TX',
            source: 'Google LSA'
        }
    },
    roofing: {
        slug: 'roofing',
        label: 'Roofing',
        pain: 'Storm leads go cold overnight',
        fix: 'Every storm lead contacted within 60s',
        demoLead: {
            name: 'Sarah Chen',
            issue: 'Storm damage assessment needed',
            city: 'Atlanta GA',
            source: 'Angi'
        }
    },
    plumbing: {
        slug: 'plumbing',
        label: 'Plumbing',
        pain: 'Emergency leads expect instant response',
        fix: 'Emergency triage + dispatch in under 2 mins',
        demoLead: {
            name: 'Carlos Rivera',
            issue: 'Burst pipe · needs immediate help',
            city: 'Phoenix AZ',
            source: 'Phone'
        }
    },
    pest_control: {
        slug: 'pest_control',
        label: 'Pest Control',
        pain: 'Recurring clients churn silently',
        fix: 'Auto re-booking sequences 30 days before renewal',
        demoLead: {
            name: 'Emma Davis',
            issue: 'Termite inspection + annual contract',
            city: 'Tampa FL',
            source: 'Web Form'
        }
    }
} as const;

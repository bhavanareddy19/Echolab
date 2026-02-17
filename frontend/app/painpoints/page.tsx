'use client';

import { Dashboard } from '@/components/Dashboard';
import CustomerPainPoints from '@/components/CustomerPainPoints';
import Breadcrumb from '@/components/UI/Breadcrumb';

export default function PainpointsPage() {
    return (
        <Dashboard>
            <div className="flex flex-col gap-5">
                <Breadcrumb
                    items={[
                        { label: 'Dashboard', href: '/' },
                        { label: 'Pain Points', isActive: true },
                    ]}
                />
                <CustomerPainPoints />
            </div>
        </Dashboard>
    );
}

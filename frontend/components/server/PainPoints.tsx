import React from 'react';

export const PainPoints = ({
    vertical,
    pain,
    fix
}: {
    vertical: string,
    pain: string,
    fix: string
}) => {
    return (
        <section className="py-20 px-6 bg-slate-900 border-y border-slate-800">
            <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-6">
                        The {vertical} Problem
                    </h2>
                    <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-2xl mb-8">
                        <p className="text-xl text-red-200 font-medium">
                            "{pain}"
                        </p>
                    </div>
                </div>
                <div>
                    <h2 className="text-3xl font-bold text-white mb-6">
                        The Automedge Fix
                    </h2>
                    <div className="p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl">
                        <p className="text-xl text-emerald-200 font-medium">
                            "{fix}"
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
};

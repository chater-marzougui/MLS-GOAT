import React, { useState } from 'react';
import { useAuth } from '../lib/auth';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
    const [name, setName] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await login(name, password);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: 'var(--background)' }}>
            <div className="w-full max-w-md">
                {/* Logo Section */}
                <div className="text-center mb-8">
                    <div className="flex justify-center items-center gap-4 mb-4">
                        <img src="/icons/logo_mls.png" alt="MLS Logo" className="h-16" />
                        <img src="/icons/logo_goat.png" alt="GOAT Logo" className="h-16" />
                    </div>
                    <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--primary)' }}>
                        GOAT 1.0
                    </h1>
                    <p className="text-lg" style={{ color: 'var(--foreground)' }}>
                        Gathering of AI Talents
                    </p>
                </div>

                {/* Login Card */}
                <div
                    className="rounded-lg p-8 shadow-xl border"
                    style={{
                        backgroundColor: 'var(--card)',
                        borderColor: 'var(--border)'
                    }}
                >
                    <h2 className="text-2xl font-semibold mb-6" style={{ color: 'var(--foreground)' }}>
                        Sign In
                    </h2>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--foreground)' }}>
                                Team Name
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                                style={{
                                    backgroundColor: 'var(--background)',
                                    borderColor: 'var(--border)',
                                    color: 'var(--foreground)',
                                }}
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--foreground)' }}>
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                                style={{
                                    backgroundColor: 'var(--background)',
                                    borderColor: 'var(--border)',
                                    color: 'var(--foreground)',
                                }}
                                required
                            />
                        </div>

                        {error && (
                            <div className="p-3 rounded-md" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#EF4444' }}>
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-3 rounded-md font-semibold transition-all hover:opacity-90 disabled:opacity-50"
                            style={{
                                backgroundColor: 'var(--primary)',
                                color: 'var(--background)',
                            }}
                        >
                            {isLoading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Login;

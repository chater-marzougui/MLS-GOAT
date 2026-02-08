import React, { useState } from 'react';
import { useAuth } from '../lib/auth';
import { useNavigate } from 'react-router-dom';
import Leaderboard from '../components/Leaderboard';
import CombinedLeaderboard from '../components/CombinedLeaderboard';
import SubmissionHistory from '../components/SubmissionHistory';
import ThemeToggle from '../components/ThemeToggle';
import QASection from '../components/QASection';

const TeamDashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<'leaderboard' | 'submissions' | 'qa'>('leaderboard');
    const [activeTask, setActiveTask] = useState<1 | 2 | 'combined'>(1);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="min-h-screen" style={{ backgroundColor: 'var(--background)' }}>
            {/* Header */}
            <header
                className="border-b"
                style={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)'
                }}
            >
                <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <img src="/icons/logo_goat.png" alt="GOAT Logo" className="h-10" />
                        <div>
                            <h1 className="text-xl font-bold" style={{ color: 'var(--primary)' }}>
                                GOAT 1.0
                            </h1>
                            <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                                Gathering of AI Talents
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <span style={{ color: 'var(--foreground)' }}>
                            Welcome, <strong>{user?.name}</strong>
                        </span>
                        <ThemeToggle />
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 rounded-md transition-all hover:opacity-80"
                            style={{
                                backgroundColor: 'var(--accent)',
                                color: 'var(--stark-white)',
                            }}
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-8">
                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    <button
                        onClick={() => setActiveTab('leaderboard')}
                        className="px-6 py-3 rounded-md font-semibold transition-all"
                        style={{
                            backgroundColor: activeTab === 'leaderboard' ? 'var(--primary)' : 'var(--card)',
                            color: activeTab === 'leaderboard' ? 'var(--background)' : 'var(--foreground)',
                        }}
                    >
                        Leaderboard
                    </button>
                    <button
                        onClick={() => setActiveTab('submissions')}
                        className="px-6 py-3 rounded-md font-semibold transition-all"
                        style={{
                            backgroundColor: activeTab === 'submissions' ? 'var(--primary)' : 'var(--card)',
                            color: activeTab === 'submissions' ? 'var(--background)' : 'var(--foreground)',
                        }}
                    >
                        My Submissions
                    </button>
                    <button
                        onClick={() => setActiveTab('qa')}
                        className="px-6 py-3 rounded-md font-semibold transition-all"
                        style={{
                            backgroundColor: activeTab === 'qa' ? 'var(--primary)' : 'var(--card)',
                            color: activeTab === 'qa' ? 'var(--background)' : 'var(--foreground)',
                        }}
                    >
                        Q&A Forum
                    </button>
                </div>

                {/* Content */}
                <div
                    className="rounded-lg border p-6"
                    style={{
                        backgroundColor: 'var(--card)',
                        borderColor: 'var(--border)',
                    }}
                >
                    {activeTab === 'leaderboard' && (
                        <>
                            {/* Task Selector */}
                            <div className="flex gap-2 mb-6">
                                <button
                                    onClick={() => setActiveTask('combined')}
                                    className="px-4 py-2 rounded-md font-medium transition-all"
                                    style={{
                                        backgroundColor: activeTask === 'combined' ? 'var(--electric-cyan)' : 'transparent',
                                        color: activeTask === 'combined' ? 'var(--background)' : 'var(--foreground)',
                                        border: `1px solid ${activeTask === 'combined' ? 'var(--electric-cyan)' : 'var(--border)'}`,
                                    }}
                                >
                                    🏆 Combined Leaderboard
                                </button>
                                <button
                                    onClick={() => setActiveTask(1)}
                                    className="px-4 py-2 rounded-md font-medium transition-all"
                                    style={{
                                        backgroundColor: activeTask === 1 ? 'var(--primary)' : 'transparent',
                                        color: activeTask === 1 ? 'var(--background)' : 'var(--foreground)',
                                        border: `1px solid ${activeTask === 1 ? 'var(--primary)' : 'var(--border)'}`,
                                    }}
                                >
                                    Task 1: Image Reconstruction
                                </button>
                                <button
                                    onClick={() => setActiveTask(2)}
                                    className="px-4 py-2 rounded-md font-medium transition-all"
                                    style={{
                                        backgroundColor: activeTask === 2 ? 'var(--accent)' : 'transparent',
                                        color: activeTask === 2 ? 'var(--stark-white)' : 'var(--foreground)',
                                        border: `1px solid ${activeTask === 2 ? 'var(--accent)' : 'var(--border)'}`,
                                    }}
                                >
                                    Task 2: Model Optimization
                                </button>
                            </div>
                            {activeTask === 'combined' ? (
                                <CombinedLeaderboard />
                            ) : (
                                <Leaderboard taskId={activeTask} />
                            )}
                        </>
                    )}

                    {activeTab === 'submissions' && <SubmissionHistory />}

                    {activeTab === 'qa' && <QASection />}
                </div>
            </main>
        </div>
    );
};

export default TeamDashboard;

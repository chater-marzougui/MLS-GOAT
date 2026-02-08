import React, { useState, useEffect } from 'react';
import { useAuth } from '../lib/auth';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '../lib/api';
import type { Team, Submission } from '../lib/types';
import ManageTeams from '../components/ManageTeams';
import SubmissionsList from '../components/SubmissionsList';
import AdminSettings from '../components/AdminSettings';
import ThemeToggle from '../components/ThemeToggle';
import QASection from '../components/QASection';

const AdminDashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [teams, setTeams] = useState<Team[]>([]);
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [activeTab, setActiveTab] = useState<'settings' | 'teams' | 'submissions' | 'qa'>('settings');

    useEffect(() => {
        if (!user?.is_admin) {
            navigate('/dashboard');
            return;
        }

        fetchTeams();
        fetchSubmissions();
    }, [user, navigate]);

    const fetchTeams = async () => {
        try {
            const response = await adminAPI.getTeams();
            setTeams(response.data);
        } catch (error) {
            console.error('Failed to fetch teams:', error);
        }
    };

    const fetchSubmissions = async () => {
        try {
            const response = await adminAPI.getAllSubmissions();
            setSubmissions(response.data);
        } catch (error) {
            console.error('Failed to fetch submissions:', error);
        }
    };

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
                        <img src="/icons/logo_mls.png" alt="MLS Logo" className="h-10" />
                        <div>
                            <h1 className="text-xl font-bold" style={{ color: 'var(--primary)' }}>
                                Admin Dashboard
                            </h1>
                            <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                                GOAT 1.0 Management
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <span style={{ color: 'var(--foreground)' }}>
                            <strong>{user?.name}</strong> (Admin)
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
                <div className="flex gap-2 mb-6 border-b" style={{ borderColor: 'var(--border)' }}>
                    <button
                        onClick={() => setActiveTab('settings')}
                        className="px-6 py-3 font-semibold transition-all"
                        style={{
                            color: activeTab === 'settings' ? 'var(--primary)' : 'var(--muted-foreground)',
                            borderBottom: activeTab === 'settings' ? '2px solid var(--primary)' : '2px solid transparent',
                        }}
                    >
                        Settings
                    </button>
                    <button
                        onClick={() => setActiveTab('teams')}
                        className="px-6 py-3 font-semibold transition-all"
                        style={{
                            color: activeTab === 'teams' ? 'var(--primary)' : 'var(--muted-foreground)',
                            borderBottom: activeTab === 'teams' ? '2px solid var(--primary)' : '2px solid transparent',
                        }}
                    >
                        Manage Teams ({teams.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('submissions')}
                        className="px-6 py-3 font-semibold transition-all"
                        style={{
                            color: activeTab === 'submissions' ? 'var(--primary)' : 'var(--muted-foreground)',
                            borderBottom: activeTab === 'submissions' ? '2px solid var(--primary)' : '2px solid transparent',
                        }}
                    >
                        Submissions ({submissions.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('qa')}
                        className="px-6 py-3 font-semibold transition-all"
                        style={{
                            color: activeTab === 'qa' ? 'var(--primary)' : 'var(--muted-foreground)',
                            borderBottom: activeTab === 'qa' ? '2px solid var(--primary)' : '2px solid transparent',
                        }}
                    >
                        Q&A Forum
                    </button>
                </div>

                {/* Tab Content */}
                {activeTab === 'settings' && <AdminSettings />}

                {activeTab === 'teams' && (
                    <ManageTeams
                        teams={teams}
                        fetchSubmissions={fetchSubmissions}
                        fetchTeams={fetchTeams}
                    />
                )}

                {activeTab === 'submissions' && (
                    <SubmissionsList
                        submissions={submissions}
                        fetchSubmissions={fetchSubmissions}
                    />
                )}

                {activeTab === 'qa' && <QASection />}
            </main>
        </div>
    );
};

export default AdminDashboard;

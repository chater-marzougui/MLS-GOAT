import React, { useEffect, useState } from 'react';
import { teamsAPI, leaderboardAPI } from '../lib/api';
import type { Submission } from '../lib/types';

const SubmissionHistory: React.FC = () => {
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [selectedTask, setSelectedTask] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [showPrivate, setShowPrivate] = useState(false);
    const [selectedDetails, setSelectedDetails] = useState<string | null>(null);

    useEffect(() => {
        const fetchSubmissions = async () => {
            setIsLoading(true);
            try {
                // Fetch settings to check if private scores should be shown
                const settingsResponse = await leaderboardAPI.getSettings();
                setShowPrivate(settingsResponse.data.show_private_scores);
                
                const response = selectedTask
                    ? await teamsAPI.getMySubmissionsByTask(selectedTask)
                    : await teamsAPI.getMySubmissions();
                setSubmissions(response.data);
            } catch (error) {
                console.error('Failed to fetch submissions:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchSubmissions();
    }, [selectedTask]);

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    const formatDetails = (details: string) => {
        try {
            const parsed = JSON.parse(details);
            return Object.entries(parsed)
                .map(([key, value]) => {
                    if (typeof value === 'number') {
                        return `${key}: ${typeof value === 'number' && value < 1 ? value.toFixed(8) : value}`;
                    }
                    return `${key}: ${value}`;
                })
                .join('\n');
        } catch {
            return details;
        }
    };

    const getDetailsPreview = (details: string) => {
        try {
            const parsed = JSON.parse(details);
            if (parsed.status) {
                return `Status: ${parsed.status}`;
            }
            if (parsed.score !== undefined) {
                return `Score: ${parsed.score.toFixed(4)}`;
            }
            return 'View details';
        } catch {
            return 'View details';
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center p-8">
                <div className="text-lg" style={{ color: 'var(--muted-foreground)' }}>Loading...</div>
            </div>
        );
    }

    return (
        <div>
            {/* Challenge Selector */}
            <div className="flex gap-2 mb-6">
                <button
                    onClick={() => setSelectedTask(null)}
                    className="px-4 py-2 rounded-md font-medium transition-all"
                    style={{
                        backgroundColor: selectedTask === null ? 'var(--primary)' : 'transparent',
                        color: selectedTask === null ? 'var(--background)' : 'var(--foreground)',
                        border: `1px solid ${selectedTask === null ? 'var(--primary)' : 'var(--border)'}`,
                    }}
                >
                    All Challenges
                </button>
                <button
                    onClick={() => setSelectedTask(1)}
                    className="px-4 py-2 rounded-md font-medium transition-all"
                    style={{
                        backgroundColor: selectedTask === 1 ? 'var(--primary)' : 'transparent',
                        color: selectedTask === 1 ? 'var(--background)' : 'var(--foreground)',
                        border: `1px solid ${selectedTask === 1 ? 'var(--primary)' : 'var(--border)'}`,
                    }}
                >
                    Challenge 1
                </button>
                <button
                    onClick={() => setSelectedTask(2)}
                    className="px-4 py-2 rounded-md font-medium transition-all"
                    style={{
                        backgroundColor: selectedTask === 2 ? 'var(--accent)' : 'transparent',
                        color: selectedTask === 2 ? 'var(--stark-white)' : 'var(--foreground)',
                        border: `1px solid ${selectedTask === 2 ? 'var(--accent)' : 'var(--border)'}`,
                    }}
                >
                    Challenge 2
                </button>
            </div>

            {/* Submissions Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                            <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Challenge</th>
                            <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Public Score</th>
                            <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Details</th>
                            {showPrivate && (
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Private Score</th>
                            )}
                            <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Submitted</th>
                        </tr>
                    </thead>
                    <tbody>
                        {submissions.length === 0 ? (
                            <tr>
                                <td colSpan={showPrivate ? 5 : 4} className="text-center p-8" style={{ color: 'var(--muted-foreground)' }}>
                                    No submissions yet
                                </td>
                            </tr>
                        ) : (
                            submissions.map((sub) => (
                                <tr
                                    key={sub.id}
                                    className="border-b hover:bg-opacity-50 transition-colors"
                                    style={{ borderColor: 'var(--border)' }}
                                >
                                    <td className="p-4" style={{ color: 'var(--foreground)' }}>
                                        <span
                                            className="px-2 py-1 rounded text-sm font-semibold"
                                            style={{
                                                backgroundColor: sub.task_id === 1 ? 'rgba(17, 197, 232, 0.2)' : 'rgba(139, 57, 186, 0.2)',
                                                color: sub.task_id === 1 ? 'var(--primary)' : 'var(--accent)'
                                            }}
                                        >
                                            Challenge {sub.task_id}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right font-mono" style={{ color: 'var(--primary)' }}>
                                        {sub.public_score.toFixed(8)}
                                    </td>
                                    <td className="p-4 text-xs" style={{ color: 'var(--muted-foreground)' }}>
                                        <button
                                            onClick={() => setSelectedDetails(sub.details)}
                                            className="px-3 py-1 rounded text-xs font-medium transition-all hover:opacity-80 underline decoration-dotted"
                                            style={{
                                                backgroundColor: 'rgba(17, 197, 232, 0.1)',
                                                color: 'var(--primary)',
                                            }}
                                        >
                                            {getDetailsPreview(sub.details)}
                                        </button>
                                    </td>
                                    {showPrivate && (
                                        <td className="p-4 text-right font-mono" style={{ color: 'var(--accent)' }}>
                                            {sub.private_score.toFixed(8)}
                                        </td>
                                    )}
                                    <td className="p-4 text-sm" style={{ color: 'var(--muted-foreground)' }}>
                                        {formatDate(sub.timestamp)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Details Modal */}
            {selectedDetails && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
                    onClick={() => setSelectedDetails(null)}
                >
                    <div
                        className="rounded-lg border p-6 max-w-2xl max-h-[80vh] overflow-auto"
                        style={{
                            backgroundColor: 'var(--card)',
                            borderColor: 'var(--border)',
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold" style={{ color: 'var(--primary)' }}>
                                Submission Details
                            </h3>
                            <button
                                onClick={() => setSelectedDetails(null)}
                                className="px-3 py-1 rounded text-sm font-medium transition-all hover:opacity-80"
                                style={{
                                    backgroundColor: 'var(--muted)',
                                    color: 'var(--foreground)',
                                }}
                            >
                                ✕ Close
                            </button>
                        </div>
                        <pre
                            className="p-4 rounded text-sm whitespace-pre-wrap break-words"
                            style={{
                                backgroundColor: 'var(--background)',
                                color: 'var(--foreground)',
                                border: '1px solid var(--border)',
                            }}
                        >
                            {formatDetails(selectedDetails)}
                        </pre>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SubmissionHistory;

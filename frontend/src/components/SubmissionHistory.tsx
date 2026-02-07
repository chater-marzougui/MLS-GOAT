import React, { useEffect, useState } from 'react';
import { teamsAPI, leaderboardAPI } from '../lib/api';
import type { Submission } from '../lib/types';

const SubmissionHistory: React.FC = () => {
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [selectedTask, setSelectedTask] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [showPrivate, setShowPrivate] = useState(false);

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
                                    <td className="p-4 text-xs max-w-xs truncate" style={{ color: 'var(--muted-foreground)' }} title={sub.details}>
                                        {sub.details}
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
        </div>
    );
};

export default SubmissionHistory;

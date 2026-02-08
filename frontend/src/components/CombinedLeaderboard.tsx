import React, { useEffect, useState } from 'react';
import { leaderboardAPI } from '../lib/api';
import type { CombinedLeaderboardEntry } from '@/lib/types';

const CombinedLeaderboard: React.FC = () => {
    const [data, setData] = useState<CombinedLeaderboardEntry[]>([]);
    const [showPrivate, setShowPrivate] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                // Fetch leaderboard settings to check if private scores should be shown
                const settingsResponse = await leaderboardAPI.getSettings();
                const privateScoresEnabled = settingsResponse.data.show_private_scores;
                
                const response = await leaderboardAPI.getCombined();
                setData(response.data);

                // Only show private scores if enabled in settings AND data has private scores
                if (privateScoresEnabled && response.data.length > 0 && response.data[0].private_combined_score !== undefined) {
                    setShowPrivate(true);
                    // Sort by private combined score in descending order
                    setData(prevData => [...prevData].sort((a, b) => {
                        const scoreA = a.private_combined_score ?? -Infinity;
                        const scoreB = b.private_combined_score ?? -Infinity;
                        return scoreB - scoreA; // Descending order (highest first)
                    }));    
                } else {
                    setShowPrivate(false);
                }
            } catch (error) {
                console.error('Failed to fetch combined leaderboard:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const getRankColor = (rank: number) => {
        if (rank === 1) return 'var(--electric-cyan)';
        if (rank === 2) return '#C0C0C0';
        if (rank === 3) return '#CD7F32';
        return 'var(--foreground)';
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center p-8">
                <div className="text-lg" style={{ color: 'var(--muted-foreground)' }}>Loading...</div>
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <div className="mb-4 p-4 rounded-lg" style={{ backgroundColor: 'var(--card)', border: '1px solid var(--border)' }}>
                <h3 className="font-semibold mb-2" style={{ color: 'var(--primary)' }}>Score Calculation</h3>
                <p style={{ color: 'var(--muted-foreground)' }}>
                    Combined Score = (Task 1 × 0.6) + (Task 2 × 0.3) + (IRL Presentations × 0.1)
                </p>
            </div>
            
            <table className="w-full">
                <thead>
                    <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                        <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Rank</th>
                        <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Team</th>
                        <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>
                            Combined Score
                        </th>
                        <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>
                            Task 1 (60%)
                        </th>
                        <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>
                            Task 2 (30%)
                        </th>
                        {showPrivate && (
                            <>
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--accent)' }}>
                                    Private Combined
                                </th>
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--accent)' }}>
                                    Private Task 1
                                </th>
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--accent)' }}>
                                    Private Task 2
                                </th>
                            </>
                        )}
                    </tr>
                </thead>
                <tbody>
                    {data.length === 0 ? (
                        <tr>
                            <td colSpan={showPrivate ? 8 : 5} className="text-center p-8" style={{ color: 'var(--muted-foreground)' }}>
                                No submissions yet
                            </td>
                        </tr>
                    ) : (
                        data.map((entry) => (
                            <tr
                                key={entry.rank}
                                className="border-b hover:bg-opacity-50 transition-colors"
                                style={{ borderColor: 'var(--border)' }}
                            >
                                <td className="p-4 font-bold" style={{ color: getRankColor(entry.rank) }}>
                                    #{entry.rank}
                                </td>
                                <td className="p-4" style={{ color: 'var(--foreground)' }}>
                                    {entry.team_name}
                                </td>
                                <td className="p-4 text-right font-mono font-bold" style={{ color: 'var(--primary)' }}>
                                    {entry.combined_score.toFixed(8)}
                                </td>
                                <td className="p-4 text-right font-mono" style={{ color: 'var(--muted-foreground)' }}>
                                    {entry.task1_score?.toFixed(8) || 'N/A'}
                                </td>
                                <td className="p-4 text-right font-mono" style={{ color: 'var(--muted-foreground)' }}>
                                    {entry.task2_score?.toFixed(8) || 'N/A'}
                                </td>
                                {showPrivate && (
                                    <>
                                        <td className="p-4 text-right font-mono font-bold" style={{ color: 'var(--accent)' }}>
                                            {entry.private_combined_score?.toFixed(8) || 'N/A'}
                                        </td>
                                        <td className="p-4 text-right font-mono" style={{ color: 'var(--accent)' }}>
                                            {entry.private_task1_score?.toFixed(8) || 'N/A'}
                                        </td>
                                        <td className="p-4 text-right font-mono" style={{ color: 'var(--accent)' }}>
                                            {entry.private_task2_score?.toFixed(8) || 'N/A'}
                                        </td>
                                    </>
                                )}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default CombinedLeaderboard;

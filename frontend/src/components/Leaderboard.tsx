import React, { useEffect, useState } from 'react';
import { leaderboardAPI } from '../lib/api';
import type { LeaderboardEntry } from '@/lib/types';

interface LeaderboardProps {
    taskId: 1 | 2;
}

const Leaderboard: React.FC<LeaderboardProps> = ({ taskId }) => {
    const [data, setData] = useState<LeaderboardEntry[]>([]);
    const [showPrivate, setShowPrivate] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const response = taskId === 1
                    ? await leaderboardAPI.getTask1()
                    : await leaderboardAPI.getTask2();
                setData(response.data);

                // Check if private scores are available
                if (response.data.length > 0 && response.data[0].private_score !== undefined) {
                    setShowPrivate(true);
                }
            } catch (error) {
                console.error('Failed to fetch leaderboard:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, [taskId]);

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
            <table className="w-full">
                <thead>
                    <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                        <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Rank</th>
                        <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Team</th>
                        <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>
                            Public Score {taskId === 1 ? '(dB)' : ''}
                        </th>
                        {showPrivate && (
                            <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>
                                Private Score {taskId === 1 ? '(dB)' : ''}
                            </th>
                        )}
                    </tr>
                </thead>
                <tbody>
                    {data.length === 0 ? (
                        <tr>
                            <td colSpan={showPrivate ? 4 : 3} className="text-center p-8" style={{ color: 'var(--muted-foreground)' }}>
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
                                <td className="p-4 text-right font-mono" style={{ color: 'var(--primary)' }}>
                                    {entry.score.toFixed(4)}
                                </td>
                                {showPrivate && (
                                    <td className="p-4 text-right font-mono" style={{ color: 'var(--accent)' }}>
                                        {entry.private_score?.toFixed(4) || 'N/A'}
                                    </td>
                                )}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default Leaderboard;

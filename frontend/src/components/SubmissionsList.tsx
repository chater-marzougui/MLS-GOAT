import { adminAPI } from '@/lib/api';
import type { Submission } from '@/lib/types';
import { useState } from 'react';


interface SubmissionsListProps {
    submissions: Submission[];
    fetchSubmissions: () => void;
}

const SubmissionsList: React.FC<SubmissionsListProps> = ({ submissions, fetchSubmissions }) => {
    const [selectedDetails, setSelectedDetails] = useState<string | null>(null);

    const handleDeleteSubmission = async (submissionId: number) => {
        if (!confirm('Are you sure you want to delete this submission?')) {
            return;
        }

        try {
            await adminAPI.deleteSubmission(submissionId);
            fetchSubmissions();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to delete submission');
        }
    };

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

    return (
        <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
            <div
                className="rounded-lg border p-6"
                style={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                }}
            >
                <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--primary)' }}>
                    Recent Submissions ({submissions.length})
                </h2>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>ID</th>
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Team ID</th>
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Challenge</th>
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Public Score</th>
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Private Score</th>
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Details</th>
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Submitted</th>
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {submissions.map((sub) => (
                                <tr
                                    key={sub.id}
                                    className="border-b hover:bg-opacity-50 transition-colors"
                                    style={{ borderColor: 'var(--border)' }}
                                >
                                    <td className="p-4" style={{ color: 'var(--muted-foreground)' }}>
                                        {sub.id}
                                    </td>
                                    <td className="p-4" style={{ color: 'var(--muted-foreground)' }}>
                                        {sub.team_id}
                                    </td>
                                    <td className="p-4">
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
                                    <td className="p-4 text-right font-mono" style={{ color: 'var(--accent)' }}>
                                        {sub.private_score.toFixed(8)}
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
                                    <td className="p-4 text-sm" style={{ color: 'var(--muted-foreground)' }}>
                                        {formatDate(sub.timestamp)}
                                    </td>
                                    <td className="p-4 text-right">
                                        <button
                                            onClick={() => handleDeleteSubmission(sub.id)}
                                            className="px-3 py-1 rounded text-sm font-medium transition-all hover:opacity-80"
                                            style={{
                                                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                                                color: '#EF4444',
                                            }}
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
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
}

export default SubmissionsList;
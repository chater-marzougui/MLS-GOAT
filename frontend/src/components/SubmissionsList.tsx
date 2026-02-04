import { adminAPI } from '@/lib/api';
import type { Submission } from '@/lib/types';


interface SubmissionsListProps {
    submissions: Submission[];
    fetchSubmissions: () => void;
}

const SubmissionsList: React.FC<SubmissionsListProps> = ({ submissions, fetchSubmissions }) => {

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
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Filename</th>
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Public Score</th>
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
                                    <td className="p-4 font-mono text-sm" style={{ color: 'var(--foreground)' }}>
                                        {sub.filename}
                                    </td>
                                    <td className="p-4 text-right font-mono" style={{ color: 'var(--primary)' }}>
                                        {sub.public_score.toFixed(4)}
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
        </div>
    );
}

export default SubmissionsList;
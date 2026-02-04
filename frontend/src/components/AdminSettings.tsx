import { adminAPI } from '@/lib/api';
import { useState, useEffect } from 'react';

const AdminSettings: React.FC = () => {
    const [showPrivateScores, setShowPrivateScores] = useState(false);

    useEffect(() => {
        fetchSettings();
    }, []);

    const handleTogglePrivateScores = async () => {
        try {
            const newValue = !showPrivateScores;
            await adminAPI.updateLeaderboardSettings(newValue);
            setShowPrivateScores(newValue);
        } catch (error) {
            console.error('Failed to update settings:', error);
        }
    };


    const fetchSettings = async () => {
        try {
            const response = await adminAPI.getLeaderboardSettings();
            setShowPrivateScores(response.data.show_private_scores);
        } catch (error) {
            console.error('Failed to fetch settings:', error);
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
            {/* Leaderboard Settings */}
            <div
                className="rounded-lg border p-6"
                style={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                }}
            >
                <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--primary)' }}>
                    Leaderboard Settings
                </h2>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="font-medium" style={{ color: 'var(--foreground)' }}>
                            Show Private Scores
                        </p>
                        <p className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                            Toggle visibility of private scores on the leaderboard
                        </p>
                    </div>
                    <button
                        onClick={handleTogglePrivateScores}
                        className="px-6 py-2 rounded-md font-semibold transition-all"
                        style={{
                            backgroundColor: showPrivateScores ? 'var(--primary)' : 'var(--muted)',
                            color: showPrivateScores ? 'var(--background)' : 'var(--foreground)',
                        }}
                    >
                        {showPrivateScores ? 'Enabled' : 'Disabled'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default AdminSettings;
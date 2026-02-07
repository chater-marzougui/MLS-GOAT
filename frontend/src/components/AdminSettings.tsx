import { adminAPI } from '@/lib/api';
import { useState, useEffect } from 'react';

const AdminSettings: React.FC = () => {
    const [showPrivateScores, setShowPrivateScores] = useState(false);
    const [isCalculating, setIsCalculating] = useState(false);
    const [calculationResult, setCalculationResult] = useState<string>('');

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

    const handleCalculatePrivateLeaderboard = async () => {
        if (!confirm('⚠️ This will evaluate all teams\' best models on the private test set.\n\nThis process may take a while. Continue?')) {
            return;
        }

        setIsCalculating(true);
        setCalculationResult('');

        try {
            const response = await adminAPI.calculatePrivateLeaderboard();
            const data = response.data;
            
            const message = `✅ Private leaderboard calculation started!\n\n` +
                `Teams processed: ${data.teams_processed || 0}\n` +
                `${data.message || ''}\n\n` +
                `Results will be available soon on the leaderboard.`;
            
            setCalculationResult(message);
            alert(message);
        } catch (error: any) {
            const errorMsg = error.response?.data?.detail || 'Failed to calculate private leaderboard';
            setCalculationResult(`❌ Error: ${errorMsg}`);
            alert(`Error: ${errorMsg}`);
        } finally {
            setIsCalculating(false);
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

            {/* Private Leaderboard Calculation */}
            <div
                className="rounded-lg border p-6"
                style={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                }}
            >
                <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--primary)' }}>
                    Private Leaderboard Calculation
                </h2>
                <div className="space-y-4">
                    <div>
                        <p className="font-medium mb-2" style={{ color: 'var(--foreground)' }}>
                            Calculate Final Private Scores
                        </p>
                        <p className="text-sm mb-4" style={{ color: 'var(--muted-foreground)' }}>
                            This will evaluate all teams' best models on the private test set. 
                            This process bypasses submission limits and can take several minutes.
                        </p>
                        <button
                            onClick={handleCalculatePrivateLeaderboard}
                            disabled={isCalculating}
                            className="px-6 py-3 rounded-md font-semibold transition-all hover:opacity-90"
                            style={{
                                backgroundColor: isCalculating ? 'var(--muted)' : 'var(--accent)',
                                color: 'var(--stark-white)',
                                cursor: isCalculating ? 'not-allowed' : 'pointer',
                            }}
                        >
                            {isCalculating ? '⏳ Calculating...' : '🚀 Calculate Private Leaderboard'}
                        </button>
                    </div>
                    
                    {calculationResult && (
                        <div
                            className="mt-4 p-4 rounded-md text-sm whitespace-pre-wrap"
                            style={{
                                backgroundColor: 'var(--background)',
                                color: 'var(--foreground)',
                                border: '1px solid var(--border)',
                            }}
                        >
                            {calculationResult}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default AdminSettings;
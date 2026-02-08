import { adminAPI } from '@/lib/api';
import { useState, useEffect } from 'react';

const AdminSettings: React.FC = () => {
    const [showPrivateScores, setShowPrivateScores] = useState(false);
    const [isCalculating, setIsCalculating] = useState(false);
    const [calculationResult, setCalculationResult] = useState<string>('');
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isChangingPassword, setIsChangingPassword] = useState(false);

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

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validation
        if (newPassword.length < 6) {
            alert('New password must be at least 6 characters long');
            return;
        }

        if (newPassword !== confirmPassword) {
            alert('New passwords do not match');
            return;
        }

        if (oldPassword === newPassword) {
            alert('New password must be different from old password');
            return;
        }

        setIsChangingPassword(true);

        try {
            await adminAPI.changePassword(oldPassword, newPassword);
            alert('✅ Password changed successfully!');
            
            // Clear form
            setOldPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (error: any) {
            const errorMsg = error.response?.data?.detail || 'Failed to change password';
            alert(`❌ Error: ${errorMsg}`);
        } finally {
            setIsChangingPassword(false);
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

            {/* Change Password */}
            <div
                className="rounded-lg border p-6"
                style={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                }}
            >
                <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--primary)' }}>
                    Change Admin Password
                </h2>
                <form onSubmit={handleChangePassword} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--foreground)' }}>
                            Old Password
                        </label>
                        <input
                            type="password"
                            value={oldPassword}
                            onChange={(e) => setOldPassword(e.target.value)}
                            className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                            style={{
                                backgroundColor: 'var(--background)',
                                borderColor: 'var(--border)',
                                color: 'var(--foreground)',
                            }}
                            required
                            disabled={isChangingPassword}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--foreground)' }}>
                            New Password
                        </label>
                        <input
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                            style={{
                                backgroundColor: 'var(--background)',
                                borderColor: 'var(--border)',
                                color: 'var(--foreground)',
                            }}
                            required
                            minLength={6}
                            disabled={isChangingPassword}
                        />
                        <p className="text-xs mt-1" style={{ color: 'var(--muted-foreground)' }}>
                            Minimum 6 characters
                        </p>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--foreground)' }}>
                            Confirm New Password
                        </label>
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                            style={{
                                backgroundColor: 'var(--background)',
                                borderColor: 'var(--border)',
                                color: 'var(--foreground)',
                            }}
                            required
                            disabled={isChangingPassword}
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={isChangingPassword}
                        className="px-6 py-2 rounded-md font-semibold transition-all hover:opacity-90"
                        style={{
                            backgroundColor: isChangingPassword ? 'var(--muted)' : 'var(--primary)',
                            color: 'var(--background)',
                            cursor: isChangingPassword ? 'not-allowed' : 'pointer',
                        }}
                    >
                        {isChangingPassword ? 'Changing...' : 'Change Password'}
                    </button>
                </form>
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
import { adminAPI } from '@/lib/api';
import { useState, useRef } from 'react';
import type { Team } from '@/lib/types';


interface ManageTeamsProps {
    teams: Team[];
    fetchSubmissions: () => void;
    fetchTeams: () => void;
}

const ManageTeams: React.FC<ManageTeamsProps> = ({ teams, fetchSubmissions, fetchTeams }) => {
    const [newTeamName, setNewTeamName] = useState('');
    const [newTeamPassword, setNewTeamPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewTeams, setPreviewTeams] = useState<Array<{ name: string; password: string }>>([]);
    const [uploadStatus, setUploadStatus] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleCreateTeam = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await adminAPI.createTeam(newTeamName, newTeamPassword);
            setNewTeamName('');
            setNewTeamPassword('');
            fetchTeams();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to create team');
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        console.log(file);
        if (!file) return;

        setSelectedFile(file);
        console.log(selectedFile);
        setUploadStatus('');

        // Parse CSV for preview
        try {
            const text = await file.text();
            const lines = text.split('\n').filter(line => line.trim());

            // Skip header
            const dataLines = lines.slice(1);

            const teams = dataLines.map(line => {
                const [name, password] = line.split(',').map(s => s.trim());
                return { name, password };
            }).filter(team => team.name && team.password);

            setPreviewTeams(teams);
        } catch (error) {
            console.error('Failed to parse CSV:', error);
            setUploadStatus('Failed to parse CSV file');
        }
    };

    const handleBatchUpload = async () => {
        console.log("handleBatchUpload");
        console.log(selectedFile);
        if (!selectedFile) return;

        setIsLoading(true);
        setUploadStatus('Uploading...');
        try {
            const response = await adminAPI.batchCreateTeams(selectedFile);
            const { created, updated, skipped, errors } = response.data;

            let message = '';

            if (created > 0) {
                message += `✅ Created ${created} new team(s)\n`;
            }
            if (updated > 0) {
                message += `🔄 Updated ${updated} team password(s)\n`;
            }
            if (skipped > 0) {
                message += `⏭️ Skipped ${skipped} unchanged team(s)\n`;
            }

            if (errors.length > 0) {
                message += `\n❌ Errors:\n${errors.join('\n')}`;
            }

            setUploadStatus(message || 'No changes made');
            fetchTeams();
            handleCancelUpload();
        } catch (error: any) {
            setUploadStatus(error.response?.data?.detail || 'Failed to upload CSV');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCancelUpload = () => {
        setSelectedFile(null);
        setPreviewTeams([]);
        setUploadStatus('');
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleDeleteTeam = async (teamId: number, teamName: string) => {
        if (!confirm(`Are you sure you want to delete team "${teamName}" and all their submissions?`)) {
            return;
        }

        try {
            await adminAPI.deleteTeam(teamId);
            fetchTeams();
            fetchSubmissions();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to delete team');
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">

            {/* Batch Upload */}
            <div
                className="rounded-lg border p-6"
                style={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                }}
            >
                <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--primary)' }}>
                    Batch Create Teams (CSV)
                </h2>
                <p className="text-sm mb-4" style={{ color: 'var(--muted-foreground)' }}>
                    Upload a CSV file with columns: <code className="px-2 py-1 rounded" style={{ backgroundColor: 'var(--background)' }}>name,password</code>
                </p>

                {/* Hidden file input */}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={handleFileSelect}
                    disabled={isLoading}
                    className="hidden"
                />

                {/* Styled upload button */}
                <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    className="px-6 py-3 rounded-md font-semibold transition-all hover:opacity-90 flex items-center gap-2"
                    style={{
                        backgroundColor: 'var(--primary)',
                        color: 'var(--background)',
                    }}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                    {selectedFile ? selectedFile.name : 'Choose CSV File'}
                </button>

                {/* Preview Table */}
                {previewTeams.length > 0 && (
                    <div className="mt-6">
                        <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--foreground)' }}>
                            Preview ({previewTeams.length} teams)
                        </h3>
                        <div className="overflow-x-auto max-h-64 overflow-y-auto border rounded" style={{ borderColor: 'var(--border)' }}>
                            <table className="w-full">
                                <thead style={{ backgroundColor: 'var(--background)', position: 'sticky', top: 0 }}>
                                    <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                                        <th className="text-left p-3 font-semibold" style={{ color: 'var(--muted-foreground)' }}>#</th>
                                        <th className="text-left p-3 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Team Name</th>
                                        <th className="text-left p-3 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Password</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {previewTeams.map((team, idx) => (
                                        <tr
                                            key={idx}
                                            className="border-b"
                                            style={{ borderColor: 'var(--border)' }}
                                        >
                                            <td className="p-3" style={{ color: 'var(--muted-foreground)' }}>
                                                {idx + 1}
                                            </td>
                                            <td className="p-3 font-medium" style={{ color: 'var(--foreground)' }}>
                                                {team.name}
                                            </td>
                                            <td className="p-3 font-mono text-sm" style={{ color: 'var(--muted-foreground)' }}>
                                                {'•'.repeat(team.password.length)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="flex gap-3 mt-4">
                            <button
                                onClick={handleBatchUpload}
                                disabled={isLoading}
                                className="px-6 py-2 rounded-md font-semibold transition-all hover:opacity-90"
                                style={{
                                    backgroundColor: 'var(--primary)',
                                    color: 'var(--background)',
                                }}
                            >
                                {isLoading ? 'Creating...' : `Create ${previewTeams.length} Teams`}
                            </button>
                            <button
                                onClick={handleCancelUpload}
                                disabled={isLoading}
                                className="px-6 py-2 rounded-md font-semibold transition-all hover:opacity-90"
                                style={{
                                    backgroundColor: 'var(--muted)',
                                    color: 'var(--foreground)',
                                }}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}

                {uploadStatus && (
                    <pre className="mt-4 p-4 rounded text-sm whitespace-pre-wrap" style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)' }}>
                        {uploadStatus}
                    </pre>
                )}
            </div>

            {/* Create Team */}
            <div
                className="rounded-lg border p-6"
                style={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                }}
            >
                <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--primary)' }}>
                    Create Single Team
                </h2>
                <form onSubmit={handleCreateTeam} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--foreground)' }}>
                                Team Name
                            </label>
                            <input
                                type="text"
                                value={newTeamName}
                                onChange={(e) => setNewTeamName(e.target.value)}
                                className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                                style={{
                                    backgroundColor: 'var(--background)',
                                    borderColor: 'var(--border)',
                                    color: 'var(--foreground)',
                                }}
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--foreground)' }}>
                                Password
                            </label>
                            <input
                                type="password"
                                value={newTeamPassword}
                                onChange={(e) => setNewTeamPassword(e.target.value)}
                                className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                                style={{
                                    backgroundColor: 'var(--background)',
                                    borderColor: 'var(--border)',
                                    color: 'var(--foreground)',
                                }}
                                required
                            />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="px-6 py-2 rounded-md font-semibold transition-all hover:opacity-90"
                        style={{
                            backgroundColor: 'var(--primary)',
                            color: 'var(--background)',
                        }}
                    >
                        {isLoading ? 'Creating...' : 'Create Team'}
                    </button>
                </form>
            </div>

            {/* Teams List */}
            <div
                className="rounded-lg border p-6"
                style={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                }}
            >
                <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--primary)' }}>
                    Teams ({teams.length})
                </h2>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>ID</th>
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Name</th>
                                <th className="text-left p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Role</th>
                                <th className="text-right p-4 font-semibold" style={{ color: 'var(--muted-foreground)' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {teams.map((team) => (
                                <tr
                                    key={team.id}
                                    className="border-b hover:bg-opacity-50 transition-colors"
                                    style={{ borderColor: 'var(--border)' }}
                                >
                                    <td className="p-4" style={{ color: 'var(--muted-foreground)' }}>
                                        {team.id}
                                    </td>
                                    <td className="p-4 font-medium" style={{ color: 'var(--foreground)' }}>
                                        {team.name}
                                    </td>
                                    <td className="p-4">
                                        <span
                                            className="px-2 py-1 rounded text-sm font-semibold"
                                            style={{
                                                backgroundColor: team.is_admin ? 'rgba(139, 57, 186, 0.2)' : 'rgba(17, 197, 232, 0.2)',
                                                color: team.is_admin ? 'var(--accent)' : 'var(--primary)',
                                            }}
                                        >
                                            {team.is_admin ? 'Admin' : 'Team'}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        {!team.is_admin && (
                                            <button
                                                onClick={() => handleDeleteTeam(team.id, team.name)}
                                                className="px-3 py-1 rounded text-sm font-medium transition-all hover:opacity-80"
                                                style={{
                                                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                                                    color: '#EF4444',
                                                }}
                                            >
                                                Delete
                                            </button>
                                        )}
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

export default ManageTeams;